"""Stage 04 API composition root; no product endpoints are exposed."""

from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.application.web import WebService
from src.infrastructure.di.bootstrap import bootstrap_di
from src.infrastructure.di.inject import resolve
from src.infrastructure.utils.config_reader import ConfigReader
from src.infrastructure.security.safe_logging import configure_logging, log_event


def create_app() -> FastAPI:
    bootstrap_di()
    config = resolve(ConfigReader)
    logger = configure_logging()

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        application.state.ready = True
        log_event(logger, "APP_START")
        try:
            yield
        finally:
            application.state.ready = False
            log_event(logger, "APP_STOP")

    app = FastAPI(
        title=config.settings.app.name,
        version=config.settings.app.version,
        lifespan=lifespan,
        docs_url=None, redoc_url=None, openapi_url=None,
    )
    app.state.ready = False

    @app.middleware("http")
    async def correlation_id(request: Request, call_next):
        request_id = str(uuid4())  # Never trust arbitrary externally supplied identifiers.
        request.state.correlation_id = request_id
        try:
            response = await call_next(request)
        except Exception:
            log_event(logger, "REQUEST_FAILED", request_id)
            response = JSONResponse(status_code=500, content={"error_code": "INTERNAL_ERROR", "correlation_id": request_id})
        response.headers["X-Correlation-ID"] = request_id
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException):
        # HTTPException.detail may contain text/credentials: never echo it.
        return JSONResponse(status_code=exc.status_code, content={"error_code": "HTTP_ERROR", "correlation_id": request.state.correlation_id})

    @app.exception_handler(RequestValidationError)
    async def input_error(request: Request, exc: RequestValidationError):
        return JSONResponse(status_code=422, content={"error_code": "VALIDATION_ERROR", "correlation_id": request.state.correlation_id})

    @app.get("/health/live", include_in_schema=False)
    async def live():
        return {"status": "alive"}

    @app.get("/health/ready", include_in_schema=False)
    async def ready():
        if not app.state.ready:
            raise HTTPException(status_code=503)
        return {"status": "ready"}

    app.include_router(resolve(WebService).api())
    return app


app = create_app()


def main() -> None:
    """Start a loopback-only service without query-string access logs."""
    import uvicorn

    bootstrap_di()
    config = resolve(ConfigReader)
    uvicorn.run(app, host=config.settings.server.host, port=config.settings.server.port, access_log=False)


if __name__ == "__main__":
    main()
