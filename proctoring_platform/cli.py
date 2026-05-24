import argparse

from proctoring_platform.core.config import get_settings
from proctoring_platform.db.session import configure_database, get_session, init_db
from proctoring_platform.seeds import bootstrap_admin, seed_sample_exam


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage the production proctoring platform backend.")
    parser.add_argument("command", choices=["init-db", "seed-sample", "bootstrap-admin"])
    args = parser.parse_args()

    settings = get_settings()
    configure_database(settings.database_url)

    if args.command == "init-db":
        init_db()
        return

    init_db()
    with get_session() as db:
        if args.command == "seed-sample":
            seed_sample_exam(db)
        elif args.command == "bootstrap-admin":
            bootstrap_admin(db, settings)


if __name__ == "__main__":
    main()
