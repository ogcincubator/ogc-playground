import json
import logging
import os
import re
from ctypes.wintypes import RECT
from datetime import datetime

import requests
from pathlib import Path
from fastapi import FastAPI, HTTPException, File, Form, Response
from fastapi.middleware.cors import CORSMiddleware
from ogc.na import ingest_json
from ogc.na.provenance import ProvenanceMetadata, FileProvenanceMetadata

logging.config.fileConfig(Path(__file__).parent / 'logging.conf', disable_existing_loggers=False)
logger = logging.getLogger('ogc_playground')

CORS_ALLOW_ORIGINS = os.environ.get('CORS_ALLOW_ORIGINS', '*').split(',')

rfa = os.environ.get('REMOTE_FETCH_ALLOWED', '').strip()
if rfa:
    REMOTE_FETCH_ALLOWED = re.compile(rfa)
    logger.info('Remote fetch allowed for "%s"', rfa)
else:
    REMOTE_FETCH_ALLOWED = None
    logger.info('Remote fetch disabled')

app = FastAPI(root_path=os.environ.get('BACKEND_ROOT_PATH', ''))

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info('Allowed CORS origins: %s', CORS_ALLOW_ORIGINS)


async def _remote_fetch(url: str) -> bytes | bool:
    if not REMOTE_FETCH_ALLOWED or not REMOTE_FETCH_ALLOWED.fullmatch(url):
        logger.warning('Remote fetch not allowed for %s', url)
        return False
    logger.info('Remote fetching %s', url)
    r = requests.get(url)
    r.raise_for_status()
    return r.content


@app.get('/remote-fetch',
         response_description='an object with a boolean `enabled` property and, optionally, a `regex`' \
                              'property to match against potential enpoints',
         )
async def remote_fetch():
    """
    Provides information about whether remote fetching of resources (e.g.
    external JSON files) is enabled and, if so, what endpoints are allowed (using
    a regular expression).
    :return: an object with a boolean `enabled` property and, optionally, a `regex`
      property to match against potential enpoints
    """
    r = {'enabled': REMOTE_FETCH_ALLOWED is not None}
    if REMOTE_FETCH_ALLOWED:
        r['regex'] = REMOTE_FETCH_ALLOWED.pattern
    return r


@app.post("/json-uplift", response_description='The output textual document depending on the selected output format')
async def json_uplift(context: bytes = File('', description='YAML contents for the uplift context definition'),
                      contexturl: str | None = Form(None, description='URL for the YAML context definition'),
                      jsondoc: bytes = File('', alias='json', description='JSON textual source document'),
                      jsonurl: str | None = Form(None, description='URL for the JSON source document'),
                      output: str | None = Form(None, description=(
                              'Type of output: `ttl` for Turtle or `expanded` for expanded JSON-LD. Otherwise,'
                              ' the transformed JSON file will be returned.')),
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
    :param output: Type of output: `ttl` for Turtle or `expanded` for expanded JSON-LD. Otherwise,
      the transformed JSON file will be returned.
    :param base: Base URI for relative URIs
    :return: The output textual document depending on the selected output format
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
        jsondoc = json.loads(jsondoc)
        g, expanded, uplifted = ingest_json.generate_graph(jsondoc, context, base)

        prov_metadata = ProvenanceMetadata(
            context=FileProvenanceMetadata(uri=contexturl),
            doc=FileProvenanceMetadata(uri=jsonurl),
            start=start,
            end=datetime.now(),
        )

        if output == 'ttl':
            if provenance:
                prov_metadata.output = FileProvenanceMetadata(uri='#', mime_type='text/turtle')
                ingest_json.generate_provenance(g, prov_metadata)
            return Response(g.serialize(format='ttl'), media_type='text/turtle')
        elif output == 'expanded':
            if provenance:
                prov_metadata.output = FileProvenanceMetadata(uri='#', mime_type='application/ld+json')
                ingest_json.add_jsonld_provenance(expanded, prov_metadata)
            return expanded
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
