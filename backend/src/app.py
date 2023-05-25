from __future__ import annotations

import io
import json
import logging.config
import os
import re
import zipfile
from datetime import datetime
from time import time
from enum import Enum

import requests
from pathlib import Path
from fastapi import FastAPI, HTTPException, File, Form, Response
from fastapi.middleware.cors import CORSMiddleware
from ogc.na import ingest_json, util as ogcnautil
from ogc.na.profile import ProfileRegistry
from ogc.na.provenance import ProvenanceMetadata, FileProvenanceMetadata
from rdflib import Graph

from yaml import load as yaml_load

try:
    from yaml import CLoader as YamlLoader
except ImportError:
    from yaml import Loader as YamlLoader

logging.config.fileConfig(Path(__file__).parent / 'logging.conf', disable_existing_loggers=False)
logger = logging.getLogger('ogc_playground')

_profile_registry: ProfileRegistry | None = None
_profiles_ts: float | None = None
PROFILE_SOURCES = ogcnautil.glob_list_split(os.environ.get('PROFILE_SOURCES', ''))
PROFILE_LOCAL_ARTIFACTS_MAPPINGS: dict[str, str] = json.loads(os.environ.get('PROFILE_LOCAL_ARTIFACTS_MAPPINGS', '{}'))
PROFILES_TTL_SECONDS = 60
logger.info('Profile sources: %s', PROFILE_SOURCES)

CORS_ALLOW_ORIGINS = os.environ.get('CORS_ALLOW_ORIGINS', '*').split(',')

rfa = os.environ.get('REMOTE_FETCH_ALLOWED', '').strip()
if rfa:
    try:
        rfa = json.loads(rfa)
        if isinstance(rfa, str):
            REMOTE_FETCH_ALLOWED = [re.compile(rfa)]
        elif isinstance(rfa, list):
            REMOTE_FETCH_ALLOWED = [re.compile(e) for e in rfa]
        else:
            raise ValueError("Unparseable REMOTE_FETCH_ALLOWED: {}".format(rfa))
    except json.JSONDecodeError:
        REMOTE_FETCH_ALLOWED = [re.compile(rfa)]
    logger.info('Remote fetch allowed for "%s"', rfa)
else:
    REMOTE_FETCH_ALLOWED = None
    logger.info('Remote fetch disabled')

rcfwl = os.environ.get('REMOTE_CONTEXT_FETCH_WHITELIST', '').strip()
if rcfwl:
    REMOTE_CONTEXT_FETCH_WHITELIST = json.loads(rcfwl)
    if isinstance(REMOTE_CONTEXT_FETCH_WHITELIST, list):
        REMOTE_CONTEXT_FETCH_WHITELIST = [w for w in REMOTE_CONTEXT_FETCH_WHITELIST if w]
else:
    REMOTE_CONTEXT_FETCH_WHITELIST = None
if REMOTE_CONTEXT_FETCH_WHITELIST is None:
    logger.warning('Remote context fetch allowed for any URL')
elif not REMOTE_CONTEXT_FETCH_WHITELIST:
    REMOTE_CONTEXT_FETCH_WHITELIST = False
    logger.info('Remote context fetch disabled')
else:
    logger.info('Remote context fetch whitelist: %s', str(REMOTE_CONTEXT_FETCH_WHITELIST))

app = FastAPI(root_path=os.environ.get('BACKEND_ROOT_PATH', ''))

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info('Allowed CORS origins: %s', CORS_ALLOW_ORIGINS)


class JsonUpliftOutputType(Enum):
    UPLIFTED = 'uplifted'
    ALL = 'all'
    EXPANDED = 'expanded'
    TURTLE = 'ttl'


async def _remote_fetch(url: str) -> bytes | bool:
    if not REMOTE_FETCH_ALLOWED or not any(e.fullmatch(url) for e in REMOTE_FETCH_ALLOWED):
        logger.warning('Remote fetch not allowed for %s', url)
        return False
    logger.info('Remote fetching %s', url)
    r = requests.get(url, headers={
        'Accept': 'application/json'
    })
    r.raise_for_status()
    return r.content


@app.get("/")
async def index():
    return {
        'name': 'OGC Playground backend'
    }


@app.get('/remote-fetch',
         response_description='an object with a boolean `enabled` property and, optionally, a `regex`'
                              'property to match against potential endpoints',
         )
async def remote_fetch():
    """
    Provides information about whether remote fetching of resources (e.g.
    external JSON files) is enabled and, if so, what endpoints are allowed (using
    a regular expression).
    :return: an object with a boolean `enabled` property and, optionally, a `regex`
      property to match against potential endpoints
    """
    r = {'enabled': bool(REMOTE_FETCH_ALLOWED)}
    if REMOTE_FETCH_ALLOWED:
        r['regex'] = (e.pattern for e in REMOTE_FETCH_ALLOWED)
    r['context'] = {}
    if REMOTE_CONTEXT_FETCH_WHITELIST is None:
        r['context']['type'] = 'open'
    elif not REMOTE_CONTEXT_FETCH_WHITELIST:
        r['context']['type'] = 'disabled'
    else:
        r['context']['type'] = 'whitelist'
        r['context']['whitelist'] = REMOTE_CONTEXT_FETCH_WHITELIST
    return r


@app.post("/json-uplift", response_description='The output textual document depending on the selected output format')
async def json_uplift(context: bytes = File('', description='YAML contents for the uplift context definition'),
                      contexturl: str | None = Form(None, description='URL for the YAML context definition'),
                      jsondoc: bytes = File('', alias='json', description='JSON textual source document'),
                      jsonurl: str | None = Form(None, description='URL for the JSON source document'),
                      output: JsonUpliftOutputType | None = Form(None, description=(
                              'Type of output: `all` for a zip file with all output types; `ttl` for Turtle; '
                              '`expanded` for expanded JSON-LD. Otherwise, the transformed JSON file will be returned.'
                      )),
                      base: str | None = Form(None, description='Base URI for relative URIs'),
                      provenance: bool = Form(True, description='Add provenance metadata')):
    """
    Performs JSON-uplift processes. The YAML context definition and/or the
    JSON source file can be provided either as textual content or as URLs
    that will be fetched (provided that remote fetching is enabled and the
    URLs match the allowed endpoints).

    :param context: YAML contents for the uplift context definition
    :param contexturl: URL for the YAML context definition
    :param jsondoc: JSON textual source document
    :param jsonurl: URL for the JSON source document
    :param output: Type of output: `all` for a zip file with all output types; `ttl` for Turtle; `expanded` for
        expanded JSON-LD. Otherwise, the transformed JSON file will be returned.
    :param base: Base URI for relative URIs
    :param provenance: Whether to include provenance metadata in the results
    :return: Output file depending on the selected output format
    """
    try:
        start = datetime.now()
        if isinstance(context, bytes):
            context = context.decode('utf-8')
        if not context and contexturl:
            context = await _remote_fetch(contexturl)
        context = ingest_json.validate_context(context=context)

        if not jsondoc:
            if jsonurl:
                jsondoc = await _remote_fetch(jsonurl)
                if jsondoc is False:
                    raise HTTPException(
                        status_code=403,
                        detail={
                            "type": "FetchForbidden",
                            "msg": "Fetch is forbidden from the requested URL",
                        }
                    )
            else:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "type": "UnprocessableEntity",
                        "msg": "No JSON source specified",
                    }
                )
        jsondoc = yaml_load(jsondoc, YamlLoader)
        g, expanded, uplifted = ingest_json.generate_graph(jsondoc, context, base,
                                                           fetch_url_whitelist=REMOTE_CONTEXT_FETCH_WHITELIST)

        if provenance:
            prov_metadata = ProvenanceMetadata(
                used=[FileProvenanceMetadata(uri=contexturl, mime_type='text/yaml', label="Context definition"),
                      FileProvenanceMetadata(uri=jsonurl, mime_type='application/json', label="JSON document")],
                start=start,
                end_auto=True,
            )
        else:
            prov_metadata = None

        if output == JsonUpliftOutputType.ALL:
            return Response(_uplift_generate_all(g, expanded, uplifted, prov_metadata), media_type='application/zip')
        if output == JsonUpliftOutputType.TURTLE:
            return Response(_uplift_generate_ttl(g, prov_metadata), media_type='text/turtle')
        elif output == JsonUpliftOutputType.EXPANDED:
            return _uplift_generate_jsonld(expanded, prov_metadata)
        else:
            return uplifted
    except HTTPException:
        raise
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "JSONDecodeError",
                "msg": "Invalid JSON input",
            }
        )
    except ingest_json.ValidationError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "ValidationError",
                "msg": e.msg,
                "index": e.index,
                "property": e.property,
                "value": e.value,
                "cause": f"{type(e.cause).__qualname__}|{str(e.cause)}" if e.cause else None
            }
        )
    except Exception as e:
        import traceback
        traceback.print_exception(e)
        raise HTTPException(
            status_code=400,
            detail={"type": type(e).__qualname__, "msg": e.msg if hasattr(e, 'msg') else str(e)}
        )


@app.get('/profiles')
async def get_profiles() -> dict:
    registry = _get_profile_registry()
    return {
        str(uri): {
            'label': profile.label,
            'token': profile.token,
            'artifacts': profile.artifacts,
        } for uri, profile in registry.profiles.items()
    }


@app.post('/entail-validate')
async def entail_validate(doc: bytes = File(description='Input document'),
                          profile_uris: list[str] = Form(description='Profile URI')):
    print(profile_uris)
    g = Graph().parse(doc)
    registry = _get_profile_registry()
    for profile_uri in profile_uris:
        if not registry.has_profile(profile_uri):
            raise HTTPException(
                status_code=400,
                detail={"type": "UnknownProfileError", "msg": "Unknown profile URI {}".format(profile_uri)}
            )

    g = registry.entail(g, additional_profiles=profile_uris)[0]
    validation_report = registry.validate(g, additional_profiles=profile_uris)

    zbuf = io.BytesIO()
    with zipfile.ZipFile(zbuf, 'a', zipfile.ZIP_DEFLATED, False) as zfile:
        zfile.writestr('entailed.ttl', g.serialize(format='ttl'))
        zfile.writestr('validation.txt', validation_report.text)
        zfile.writestr('validation.ttl', validation_report.graph.serialize(format='ttl'))
    return Response(zbuf.getvalue(), media_type='application/zip')


def _uplift_generate_ttl(g: Graph, prov_metadata: ProvenanceMetadata) -> str:
    if prov_metadata:
        prov_metadata.output = FileProvenanceMetadata(uri='#', mime_type='text/turtle')
        ingest_json.generate_provenance(g, prov_metadata)
    return g.serialize(format='ttl')


def _uplift_generate_jsonld(expanded: dict, prov_metadata: ProvenanceMetadata) -> dict:
    if prov_metadata:
        prov_metadata.output = FileProvenanceMetadata(uri='#', mime_type='application/ld+json')
        ingest_json.add_jsonld_provenance(expanded, prov_metadata)
    return expanded


def _uplift_generate_all(g: Graph, expanded: dict, uplifted: dict, prov_metadata: ProvenanceMetadata):
    ttl = _uplift_generate_ttl(g, prov_metadata)
    expanded = _uplift_generate_jsonld(expanded, prov_metadata)

    zbuf = io.BytesIO()
    with zipfile.ZipFile(zbuf, 'a', zipfile.ZIP_DEFLATED, False) as zfile:
        zfile.writestr('ttl.ttl', ttl)
        zfile.writestr('expanded.jsonld', json.dumps(expanded, indent=2))
        zfile.writestr('uplifted.jsonld', json.dumps(uplifted, indent=2))

    return zbuf.getvalue()


def _get_profile_registry() -> ProfileRegistry:
    if not PROFILE_SOURCES:
        return ProfileRegistry([])
    now = time()
    global _profile_registry
    if not _profile_registry or not _profiles_ts or now - _profiles_ts >= PROFILES_TTL_SECONDS:
        _profile_registry = ProfileRegistry(
            PROFILE_SOURCES,
            local_artifact_mappings=PROFILE_LOCAL_ARTIFACTS_MAPPINGS,
            ignore_artifact_errors=True,
        )
    return _profile_registry
