# AI-Based Online Exam Proctoring System

This repository contains two code paths:

- A production-oriented FastAPI backend in `proctoring_platform/`.
- A production React frontend in `frontend/`.
- The original Flask/OpenCV prototype preserved under `legacy/`.

New development should target `proctoring_platform/`. The legacy code is still useful because the production analyzer wraps the original OpenCV/Dlib detector functions instead of rewriting all model logic from scratch.

## Repository Layout

Top-level structure:

```text
.
├── Dockerfile                        # Backend image
├── docker-compose.yml                # Frontend + API + PostgreSQL stack
├── README.md
├── requirements.txt                  # Backend dependencies
├── alembic.ini
├── migrations/                       # Alembic migration files
├── proctoring_platform/              # Production FastAPI backend
│   ├── api/routes/                   # Auth, exams, attempts, proctoring, review, health
│   ├── core/                         # Config, security, time helpers
│   ├── db/                           # Engine, session, DB init
│   ├── services/                     # Exam logic, analyzers, policy, evidence storage
│   ├── app.py                        # FastAPI app entrypoint
│   ├── cli.py                        # DB/admin/sample-data CLI
│   ├── models.py                     # SQLAlchemy models
│   ├── schemas.py                    # Pydantic schemas
│   └── seeds.py                      # Admin bootstrap and sample exam seed
├── frontend/                         # Production Vite React TypeScript frontend
│   ├── Dockerfile                    # Frontend image
│   ├── nginx.conf                    # Nginx runtime config
│   ├── public/config.js              # Runtime API config for local dev
│   ├── docker-entrypoint.d/          # Writes runtime API config in Docker
│   └── src/
│       ├── api/                      # Frontend API client
│       ├── auth/                     # Auth context
│       ├── components/               # Shared UI components
│       └── pages/                    # Candidate/admin screens
├── legacy/                           # Original prototype and detector assets
│   ├── detectors/                    # OpenCV/Dlib/YOLO detector functions
│   ├── models/                       # Landmark and YOLO model files
│   └── prototype/                    # Original Flask demo app
└── tests/                            # Backend/API/proctoring tests
```

Key directories:

- `proctoring_platform/` - production backend package.
- `frontend/` - production Vite React TypeScript frontend for candidates and admins.
- `migrations/` - Alembic migration files for the production schema.
- `legacy/detectors/` - original OpenCV/Dlib/YOLO detector modules reused by the production analyzer.
- `legacy/models/` - Dlib face landmark model and YOLO model files.
- `legacy/prototype/` - original Flask demo app, templates, static assets, MySQL helper, and activity log.
- `tests/` - production backend tests.

## Production Backend Responsibilities

The production backend handles the server-side parts of an exam session:

- User signup/login with JWT authentication and Argon2 password hashing.
- Server-side exam, question, option, attempt, answer, score, and submission storage.
- Proctoring session creation for each exam attempt.
- Structured proctoring event ingestion and review timelines.
- Evidence metadata and local filesystem evidence storage for development.
- Frame analysis using the legacy OpenCV/Dlib/YOLO detectors.
- Audio spike detection from raw little-endian PCM16 microphone chunks.

The backend is intentionally responsible for scoring and attempt state. Correct answers are not sent to the client during an attempt.

## Production Frontend Responsibilities

The production frontend is a Vite React TypeScript app in `frontend/`.

It provides:

- Candidate signup/login.
- Candidate exam listing and attempt start.
- Server-backed question display and answer saving.
- Camera preview and periodic frame snapshot upload to `/analyze-frame`.
- Browser integrity event capture for tab switch, fullscreen exit, and network interruption.
- Admin exam creation without editing files.
- Admin review list and attempt timeline review.
- Review decision submission.

## Core Runtime Flow

1. A student signs up or logs in through `/auth/signup` or `/auth/login`.
2. The frontend lists published exams through `/exams`.
3. The student starts an attempt through `POST /attempts`.
4. The backend creates both an `exam_attempt` and a linked `proctoring_session`.
5. The frontend fetches attempt questions through `/attempts/{attempt_id}/questions`.
6. The frontend saves answers through `/attempts/{attempt_id}/answers`.
7. During the exam, the frontend sends proctoring data through one of:
   - `POST /proctoring/sessions/{session_id}/events`
   - `POST /proctoring/sessions/{session_id}/analyze-frame`
   - `POST /proctoring/sessions/{session_id}/analyze-audio`
   - `POST /proctoring/sessions/{session_id}/evidence`
8. The student submits through `POST /attempts/{attempt_id}/submit`.
9. Reviewers/instructors inspect the timeline through `/review/attempts/{attempt_id}/timeline`.
10. Reviewers/instructors record a review decision through `/review/attempts/{attempt_id}/decision`.

## Detector Flow

The production frame analyzer lives in:

`proctoring_platform/services/opencv_analyzers.py`

It imports detector functions from `legacy/detectors/`:

- `facial_detections.detectFace`
- `blink_detection.isBlinking`
- `eye_tracker.gazeDetection`
- `mouth_tracking.mouthTrack`
- `head_pose_estimation.head_pose_detection`
- `object_detection.detectObject`

The analyzer converts detector outputs into structured proctoring events:

- `NO_FACE`
- `MULTIPLE_FACES`
- `GAZE_AWAY`
- `MOUTH_OPEN`
- `HEAD_AWAY`
- `PHONE_DETECTED`
- `UNAUTHORIZED_OBJECT`

The audio analyzer lives in:

`proctoring_platform/services/audio_analyzers.py`

It emits:

- `AUDIO_SPIKE`

The event severity mapping lives in:

`proctoring_platform/services/proctoring_policy.py`

High-severity or high-confidence events can cause the uploaded frame/audio to be stored as evidence and attached to the generated events.

## Important API Endpoints

Authentication:

- `POST /auth/signup`
- `POST /auth/login`

Exam and attempt flow:

- `GET /exams`
- `GET /exams/{exam_id}`
- `POST /attempts`
- `GET /attempts/{attempt_id}`
- `GET /attempts/{attempt_id}/questions`
- `POST /attempts/{attempt_id}/answers`
- `POST /attempts/{attempt_id}/submit`

Proctoring:

- `POST /proctoring/sessions/{session_id}/events`
- `POST /proctoring/sessions/{session_id}/evidence`
- `POST /proctoring/sessions/{session_id}/analyze-frame`
- `POST /proctoring/sessions/{session_id}/analyze-audio`

Review:

- `GET /review/attempts`
- `GET /review/attempts/{attempt_id}/timeline`
- `POST /review/attempts/{attempt_id}/decision`

Health:

- `GET /health`

OpenAPI docs are available at:

`http://127.0.0.1:8000/docs`

## Run With Docker

Docker is the recommended path for this project because Dlib needs native build tools. The Docker image installs `build-essential` and `cmake`, so your local Python venv does not need to compile Dlib.

Start Docker Desktop first on macOS:

```bash
open -a Docker
```

Create local environment settings:

```bash
cp .env.example .env
```

Default `.env.example` behavior is already set up for Docker testing:

- `DATABASE_URL` points at the `postgres` service from `docker-compose.yml`.
- `AUTO_CREATE_TABLES=true` initializes the schema automatically on startup.
- `SEED_SAMPLE_DATA=true` creates a sample published exam automatically.
- `BOOTSTRAP_ADMIN_*` creates an admin user automatically on first startup.

Start the frontend, API, and PostgreSQL:

```bash
docker compose up --build -d
```

The frontend image is a production-style multi-stage build. Node builds the Vite app, then Nginx serves the static assets on port `5173`. The `API_BASE_URL` environment variable in `docker-compose.yml` writes `/config.js` at container startup, so the same frontend image can point at a different FastAPI base URL without rebuilding.

Open the frontend:

```text
http://127.0.0.1:5173
```

Open the backend API docs:

```text
http://127.0.0.1:8000/docs
```

Verify the stack is healthy:

```bash
docker compose ps
docker compose logs -f api
```

What you should expect after startup:

- `frontend` is reachable on port `5173`.
- `api` is reachable on port `8000`.
- `postgres` is healthy on port `5432`.
- The API bootstraps `admin@example.com` and seeds one sample exam.
- Evidence files written by proctoring endpoints are stored in the Docker volume mounted at `/data/evidence`.

Check logs:

```bash
docker compose logs -f api
docker compose logs -f frontend
```

Stop containers:

```bash
docker compose down
```

Remove containers and local Docker volumes:

```bash
docker compose down -v
```

Default local admin from `.env.example`:

```text
admin@example.com
change-me-now
```

Suggested Docker smoke test:

1. Open `http://127.0.0.1:5173`.
2. Log in with `admin@example.com` / `change-me-now`.
3. Confirm the seeded sample exam appears in the UI or through `GET /exams` in `http://127.0.0.1:8000/docs`.
4. Start an exam attempt and confirm proctoring requests appear in `docker compose logs -f api`.

For real use, change `JWT_SECRET` and `BOOTSTRAP_ADMIN_PASSWORD` in `.env`.

## Run Locally Without Docker

Local execution is useful for API and unit tests, but native frame detection may fail if Dlib cannot compile on your machine.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python -m proctoring_platform.cli seed-sample
uvicorn proctoring_platform.app:app --reload --port 8000
```

If Dlib is missing, `/analyze-frame` returns a service-unavailable response instead of crashing the API. Docker should be used to test the full detector stack.

Run the frontend separately when the backend is already running:

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

The standalone frontend starts at:

```text
http://127.0.0.1:5173
```

Build the frontend:

```bash
cd frontend
npm run build
```

For local Vite development, set the backend URL in `frontend/.env`:

```text
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## Database Setup

The production schema is represented by SQLAlchemy models and Alembic migrations.

Run migrations:

```bash
alembic upgrade head
```

Create tables directly through the CLI:

```bash
python -m proctoring_platform.cli init-db
```

Seed a sample exam:

```bash
python -m proctoring_platform.cli seed-sample
```

Bootstrap an admin user from environment variables:

```bash
python -m proctoring_platform.cli bootstrap-admin
```

`AUTO_CREATE_TABLES=true` is enabled in `.env.example` for local development. In production, prefer Alembic migrations and set `AUTO_CREATE_TABLES=false`.

## Testing

Run the production test suite:

```bash
pytest
```

Current tests cover:

- Proctoring policy normalization and severity decisions.
- PCM16 audio spike detection.
- Legacy detector adapter event mapping.
- Student signup, exam listing, attempt creation, answer save, proctoring event save, frame analysis persistence, audio analysis persistence, submission, and review timeline access.

Some tests inject fake detector outputs so CI does not require a webcam, Dlib, or actual image frames.

## Legacy Prototype

The original Flask demo is preserved in `legacy/prototype/`.

Run it from the repository root:

```bash
python -m legacy.prototype.server
```

The legacy prototype still has its original limitations:

- The legacy MySQL helper now reads `LEGACY_MYSQL_USER` and `LEGACY_MYSQL_PASSWORD` from the environment.
- Some behavior is platform-specific, such as `winsound`.
- The original quiz frontend keeps questions and scoring in client-side JavaScript.
- It writes activity data to a local text file.

Use it only as a reference/demo. Production work should happen in `proctoring_platform/`.

## Development Notes

- Keep API request/response contracts in `proctoring_platform/schemas.py`.
- Keep persistence models in `proctoring_platform/models.py`.
- Keep business rules outside route handlers where possible.
- Add new proctoring event types to `proctoring_platform/services/proctoring_policy.py`.
- Keep detector-specific code behind analyzer interfaces in `proctoring_platform/services/`.
- Do not move large model files into the production package; keep them under `legacy/models/` or move them to external model storage later.
- Frontend runtime API configuration is injected through `frontend/public/config.js` locally and generated by `frontend/docker-entrypoint.d/10-write-config.sh` in Docker.

## Production Hardening Still Needed

This branch is a production-oriented foundation, not a complete hosted product. Before real deployment, add:

- Object storage such as S3 for evidence instead of local filesystem storage.
- Background workers for heavy frame/video analysis.
- Rate limits and payload size limits on evidence/frame/audio endpoints.
- More granular exam authoring APIs.
- Audit log writes for sensitive operations.
- Deployment-specific secrets management.
- Monitoring, metrics, and structured logging.
- Full end-to-end browser tests.
