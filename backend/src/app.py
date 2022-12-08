import json
import logging
import os
import re
from ctypes.wintypes import RECT

import requests
from pathlib import Path
from fastapi import FastAPI, HTTPException, File, Form, Response
from fastapi.middleware.cors import CORSMiddleware
from ogc.na import ingest_json

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


@app.get('/remote-fetch')
async def remote_fetch():
    r = {'enabled': REMOTE_FETCH_ALLOWED is not None}
    if REMOTE_FETCH_ALLOWED:
        r['regex'] = REMOTE_FETCH_ALLOWED.pattern
    return r


@app.post("/json-uplift")
async def json_uplift(context: bytes = File(''),
                      contexturl: str | None = Form(None),
                      jsondoc: bytes = File('', alias='json'),
                      jsonurl: str | None = Form(None),
                      output: str | None = Form(None),
                      base: str | None = Form(None)):
    try:
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
        if output == 'ttl':
            return Response(g.serialize(format='ttl'), media_type="text/turtle")
        elif output == 'expanded':
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
