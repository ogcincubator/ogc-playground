from distutils.command.upload import upload

from fastapi import FastAPI, Body, HTTPException
from jsonschema.exceptions import ValidationError as JsonValidationError
from ogc.na import ingest_json

app = FastAPI()


@app.post("/json-uplift")
async def json_uplift(context: str | dict = Body(), jsondoc: dict = Body(), output: str | None = None,
               base: str | None = None):
    try:
        context = ingest_json.validate_context(context=context)
        g, expanded, uplifted = ingest_json.generate_graph(jsondoc, context, base)
        if output == 'ttl':
            return g.serialize(format='ttl')
        elif output == 'expanded':
            return expanded
        else:
            return uplifted
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
