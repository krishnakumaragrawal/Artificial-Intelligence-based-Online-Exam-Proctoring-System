from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from proctoring_platform.api.routes import attempts, auth, exams, health, proctoring, review
from proctoring_platform.core.config import Settings, get_settings
from proctoring_platform.db.session import configure_database, get_session, init_db
from proctoring_platform.seeds import bootstrap_admin, seed_sample_exam


def create_app(settings: Settings = None) -> FastAPI:
    app_settings = settings or get_settings()
    app_settings.validate_runtime_security()
    configure_database(app_settings.database_url)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if app_settings.auto_create_tables:
            init_db()
        with get_session() as db:
            bootstrap_admin(db, app_settings)
            if app_settings.seed_sample_data:
                seed_sample_exam(db)
        yield

    app = FastAPI(title=app_settings.app_name, version="0.1.0", lifespan=lifespan)
    app.state.settings = app_settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(app_settings.cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(exams.router)
    app.include_router(attempts.router)
    app.include_router(proctoring.router)
    app.include_router(review.router)

    return app


app = create_app()
