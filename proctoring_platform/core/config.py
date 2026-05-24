from dataclasses import dataclass
from functools import lru_cache
import os
from pathlib import Path
from typing import Tuple


def _parse_csv(value: str) -> Tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


@dataclass(frozen=True)
class Settings:
    app_name: str = "AI Exam Proctoring Platform"
    environment: str = "local"
    database_url: str = "sqlite:///./proctoring.db"
    jwt_secret: str = "change-me-before-production"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60
    cors_origins: Tuple[str, ...] = ("http://localhost:5173", "http://127.0.0.1:5173")
    evidence_dir: Path = Path("./evidence")
    auto_create_tables: bool = True
    seed_sample_data: bool = False
    bootstrap_admin_email: str = ""
    bootstrap_admin_username: str = "admin"
    bootstrap_admin_password: str = ""

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            app_name=os.getenv("APP_NAME", cls.app_name),
            environment=os.getenv("ENVIRONMENT", cls.environment),
            database_url=os.getenv("DATABASE_URL", cls.database_url),
            jwt_secret=os.getenv("JWT_SECRET", cls.jwt_secret),
            jwt_algorithm=os.getenv("JWT_ALGORITHM", cls.jwt_algorithm),
            access_token_minutes=int(os.getenv("ACCESS_TOKEN_MINUTES", str(cls.access_token_minutes))),
            cors_origins=_parse_csv(os.getenv("CORS_ORIGINS", ",".join(cls.cors_origins))),
            evidence_dir=Path(os.getenv("EVIDENCE_DIR", str(cls.evidence_dir))),
            auto_create_tables=os.getenv("AUTO_CREATE_TABLES", "true").lower() in {"1", "true", "yes"},
            seed_sample_data=os.getenv("SEED_SAMPLE_DATA", "false").lower() in {"1", "true", "yes"},
            bootstrap_admin_email=os.getenv("BOOTSTRAP_ADMIN_EMAIL", cls.bootstrap_admin_email),
            bootstrap_admin_username=os.getenv("BOOTSTRAP_ADMIN_USERNAME", cls.bootstrap_admin_username),
            bootstrap_admin_password=os.getenv("BOOTSTRAP_ADMIN_PASSWORD", cls.bootstrap_admin_password),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()
