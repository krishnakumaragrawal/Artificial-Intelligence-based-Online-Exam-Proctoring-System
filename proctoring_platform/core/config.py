from dataclasses import dataclass
from functools import lru_cache
import os
from pathlib import Path
from typing import Tuple

DEFAULT_JWT_SECRET = "change-me-before-production"
PRODUCTION_ENVIRONMENTS = {"prod", "production"}


def _parse_csv(value: str) -> Tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


@dataclass(frozen=True)
class Settings:
    app_name: str = "AI Exam Proctoring Platform"
    environment: str = "local"
    database_url: str = "sqlite:///./proctoring.db"
    jwt_secret: str = DEFAULT_JWT_SECRET
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60
    cors_origins: Tuple[str, ...] = ("http://localhost:5173", "http://127.0.0.1:5173")
    evidence_dir: Path = Path("./evidence")
    max_frame_upload_bytes: int = 1_500_000
    max_audio_upload_bytes: int = 1_000_000
    max_evidence_upload_bytes: int = 10_000_000
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
            max_frame_upload_bytes=int(os.getenv("MAX_FRAME_UPLOAD_BYTES", str(cls.max_frame_upload_bytes))),
            max_audio_upload_bytes=int(os.getenv("MAX_AUDIO_UPLOAD_BYTES", str(cls.max_audio_upload_bytes))),
            max_evidence_upload_bytes=int(os.getenv("MAX_EVIDENCE_UPLOAD_BYTES", str(cls.max_evidence_upload_bytes))),
            auto_create_tables=os.getenv("AUTO_CREATE_TABLES", "true").lower() in {"1", "true", "yes"},
            seed_sample_data=os.getenv("SEED_SAMPLE_DATA", "false").lower() in {"1", "true", "yes"},
            bootstrap_admin_email=os.getenv("BOOTSTRAP_ADMIN_EMAIL", cls.bootstrap_admin_email),
            bootstrap_admin_username=os.getenv("BOOTSTRAP_ADMIN_USERNAME", cls.bootstrap_admin_username),
            bootstrap_admin_password=os.getenv("BOOTSTRAP_ADMIN_PASSWORD", cls.bootstrap_admin_password),
        )

    def validate_runtime_security(self) -> None:
        if self.environment.strip().lower() not in PRODUCTION_ENVIRONMENTS:
            return

        if self.jwt_secret == DEFAULT_JWT_SECRET or len(self.jwt_secret) < 32:
            raise ValueError("JWT_SECRET must be set to a non-default value with at least 32 characters in production")
        if "*" in self.cors_origins:
            raise ValueError("CORS_ORIGINS cannot include '*' when ENVIRONMENT=production")
        if self.bootstrap_admin_email and self.bootstrap_admin_password in {"", "change-me-now"}:
            raise ValueError("BOOTSTRAP_ADMIN_PASSWORD must be changed or disabled in production")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()
