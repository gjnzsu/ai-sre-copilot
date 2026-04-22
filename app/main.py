from fastapi import FastAPI

from app.api.routes.analyze import router as analyze_router
from app.config.settings import get_settings


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="log-anomaly-agent",
        version="0.1.0",
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "env": settings.app_env,
        }

    app.include_router(analyze_router, prefix="/v1/log-anomaly", tags=["log-anomaly"])
    return app


app = create_app()
