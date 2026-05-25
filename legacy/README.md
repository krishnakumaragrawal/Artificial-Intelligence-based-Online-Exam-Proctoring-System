# Legacy Prototype

This folder contains the original Flask/OpenCV proof of concept.

- `prototype/` contains the original Flask app, templates, static assets, SQL helper, and activity log.
- `detectors/` contains the original OpenCV/Dlib/YOLO detector functions.
- `models/` contains the local Dlib landmark and YOLO model files used by the detectors.

The production backend imports detector functions from `legacy.detectors` through `proctoring_platform/services/opencv_analyzers.py`.

Run the legacy Flask demo from the repository root:

```bash
python -m legacy.prototype.server
```

The legacy demo still has its original local assumptions, including MySQL credentials and platform-specific audio/beep behavior.
