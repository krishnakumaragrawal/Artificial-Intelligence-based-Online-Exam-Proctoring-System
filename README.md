# AI based Online Exam Proctoring System

## Production v2 Backend

This repository now contains a production-oriented backend implementation under `proctoring_platform/`. The original Flask/OpenCV prototype files remain in place for reference, but new development should target the FastAPI service.

### What the v2 service includes

- JWT authentication with hashed passwords.
- Server-side exams, questions, options, attempts, answers, scoring, and submissions.
- Structured proctoring sessions, events, evidence metadata, and reviewer decisions.
- Server-side frame analysis that wraps the existing OpenCV/Dlib detectors for face count, gaze, mouth, head pose, and YOLO object detection.
- Server-side raw PCM16 audio spike analysis for microphone chunks.
- Docker, PostgreSQL configuration, environment-based settings, and pytest coverage for the main exam/proctoring flow.

### Run locally

Native frame analysis depends on OpenCV and Dlib. On macOS, Dlib often requires extra system build tools; Docker is the most reliable path for running the full detector stack.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python -m proctoring_platform.cli seed-sample
uvicorn proctoring_platform.app:app --reload --port 8000
```

API docs are available at `http://127.0.0.1:8000/docs`.

### Run with Docker

```bash
cp .env.example .env
docker compose up --build
```

The API starts on `http://127.0.0.1:8000` and PostgreSQL on port `5432`.

### Test

```bash
pytest
```

### Production direction

The current v2 code is the backend foundation for the scalable design:

- Keep browser-facing exam state and scoring server-side.
- Send proctoring telemetry to `/proctoring/sessions/{id}/events`.
- Upload webcam images to `/proctoring/sessions/{id}/analyze-frame` to run face, gaze, mouth, head-pose, and object detection. Suspicious results are persisted as reviewable events.
- Upload raw little-endian PCM16 microphone chunks to `/proctoring/sessions/{id}/analyze-audio` to detect audio spikes.
- Upload evidence snapshots/clips directly to `/proctoring/sessions/{id}/evidence` when the client already has a violation event.
- For larger deployments, move the same OpenCV/YOLO analyzer into a worker or separate ML service and keep emitting the same structured event shape.
- Use object storage for evidence in production; the included filesystem storage is suitable for local development and small deployments.

## Legacy Prototype

AI-Based Online Exam Proctoring System is an innovative project designed to maintain the integrity and security of online exams. Utilizing advanced artificial intelligence algorithms, this system monitors and evaluates test-takers in real-time, detecting any suspicious behavior or potential cheating attempts. Through features such as facial recognition, eye tracking, and keystroke analysis, it ensures a fair and transparent examination environment.

Moreover, the system generates a comprehensive log file named "activity.txt" that contains detailed records of all the activities and behaviors exhibited by the examinee during the examination. This log file serves as a valuable resource for educators and administrators, allowing them to review and analyze the test-taker's actions post-exam, aiding in the identification of any irregularities or concerns. With its automated monitoring capabilities and detailed activity logging, educators can confidently administer exams remotely, knowing that the integrity of the assessment process is upheld and supported by thorough documentation.

## Key Features and Functions 
1. Face Detection using Dlib
2. Eye Gaze Detection
3. Mouth Tracking
4. Blink Detection
5. Head Pose Estimation
6. Object Detection using Yolo
7. Audio Detection

## Technology Used 
1. Python
2. Comuter Vision 
3. OpenCV
4. Dlib
5. Pyaudio
6. Winsound
7. Web Skills (HTML, CSS, JS)
8. Flask Server
9. SQL Database

## Contact 
For any feedback or queries, please reach out to me at [LinkedIn](https://www.linkedin.com/in/krishnakumaragrawal/)
