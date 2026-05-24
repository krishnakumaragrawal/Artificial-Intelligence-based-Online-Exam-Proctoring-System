from io import BytesIO
from functools import lru_cache
from typing import Any, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from proctoring_platform.api.deps import get_current_user, get_request_settings
from proctoring_platform.core.config import Settings
from proctoring_platform.core.time import now_utc
from proctoring_platform.db.session import get_db
from proctoring_platform.models import EvidenceAsset, ProctoringEvent, ProctoringSession, User
from proctoring_platform.schemas import (
    AudioAnalysisResponse,
    EvidenceAssetPublic,
    FrameAnalysisResponse,
    ProctoringEventCreate,
    ProctoringEventPublic,
)
from proctoring_platform.services.audio_analyzers import PCM16AudioAnalyzer
from proctoring_platform.services.detectors import DetectorEvent, DetectorUnavailable
from proctoring_platform.services.evidence_storage import FileSystemEvidenceStore
from proctoring_platform.services.opencv_analyzers import LegacyOpenCVFrameAnalyzer
from proctoring_platform.services.proctoring_policy import policy

router = APIRouter(prefix="/proctoring/sessions", tags=["proctoring"])


def _get_owned_session(db: Session, session_id: int, user: User) -> ProctoringSession:
    session = db.query(ProctoringSession).filter(ProctoringSession.id == session_id).first()
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proctoring session not found")
    if session.attempt.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Proctoring session access denied")
    return session


@lru_cache(maxsize=1)
def get_frame_analyzer() -> LegacyOpenCVFrameAnalyzer:
    return LegacyOpenCVFrameAnalyzer()


def get_audio_analyzer() -> PCM16AudioAnalyzer:
    return PCM16AudioAnalyzer()


def _save_evidence_asset(
    db: Session,
    settings: Settings,
    session: ProctoringSession,
    filename: str,
    content_type: Optional[str],
    content: bytes,
) -> EvidenceAsset:
    store = FileSystemEvidenceStore(settings.evidence_dir)
    storage_key, byte_size, digest = store.save(session.id, filename, BytesIO(content))
    asset = EvidenceAsset(
        session_id=session.id,
        storage_key=storage_key,
        content_type=content_type or "application/octet-stream",
        byte_size=byte_size,
        sha256=digest,
    )
    db.add(asset)
    db.flush()
    return asset


def _persist_detector_event(
    db: Session,
    session: ProctoringSession,
    detector_event: DetectorEvent,
    evidence_asset: Optional[EvidenceAsset] = None,
) -> ProctoringEvent:
    event_type = policy.normalize_event_type(detector_event.event_type)
    event = ProctoringEvent(
        session_id=session.id,
        evidence_asset_id=evidence_asset.id if evidence_asset is not None else None,
        event_type=event_type,
        severity=policy.severity_for(event_type),
        confidence=detector_event.confidence,
        occurred_at=detector_event.occurred_at,
        payload=detector_event.payload,
    )
    db.add(event)
    db.flush()
    return event


@router.post("/{session_id}/events", response_model=ProctoringEventPublic)
def create_event(
    session_id: int,
    payload: ProctoringEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProctoringEvent:
    session = _get_owned_session(db, session_id, current_user)
    evidence_asset = None
    if payload.evidence_asset_id is not None:
        evidence_asset = (
            db.query(EvidenceAsset)
            .filter(EvidenceAsset.id == payload.evidence_asset_id, EvidenceAsset.session_id == session.id)
            .first()
        )
        if evidence_asset is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Evidence asset does not belong to session")

    event_type = policy.normalize_event_type(payload.event_type)
    event = ProctoringEvent(
        session_id=session.id,
        evidence_asset_id=evidence_asset.id if evidence_asset is not None else None,
        event_type=event_type,
        severity=policy.severity_for(event_type),
        confidence=payload.confidence,
        occurred_at=payload.occurred_at or now_utc(),
        payload=payload.payload,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.post("/{session_id}/evidence", response_model=EvidenceAssetPublic, status_code=status.HTTP_201_CREATED)
def upload_evidence(
    session_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_request_settings),
) -> EvidenceAsset:
    session = _get_owned_session(db, session_id, current_user)
    store = FileSystemEvidenceStore(settings.evidence_dir)
    storage_key, byte_size, digest = store.save(session.id, file.filename or "evidence.bin", file.file)

    asset = EvidenceAsset(
        session_id=session.id,
        storage_key=storage_key,
        content_type=file.content_type or "application/octet-stream",
        byte_size=byte_size,
        sha256=digest,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


@router.post("/{session_id}/analyze-frame", response_model=FrameAnalysisResponse)
def analyze_frame(
    session_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_request_settings),
    analyzer: Any = Depends(get_frame_analyzer),
) -> FrameAnalysisResponse:
    session = _get_owned_session(db, session_id, current_user)
    content = file.file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Frame upload is empty")

    try:
        analysis = analyzer.analyze_image_bytes(content)
    except DetectorUnavailable as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    should_store_evidence = any(
        policy.should_attach_evidence(event.event_type, event.confidence or 0.0)
        for event in analysis.events
    )
    evidence_asset = None
    if should_store_evidence:
        evidence_asset = _save_evidence_asset(
            db,
            settings,
            session,
            file.filename or "frame.jpg",
            file.content_type,
            content,
        )

    persisted_events = [
        _persist_detector_event(db, session, detector_event, evidence_asset)
        for detector_event in analysis.events
    ]
    db.commit()
    for event in persisted_events:
        db.refresh(event)
    if evidence_asset is not None:
        db.refresh(evidence_asset)

    return FrameAnalysisResponse(
        frame_id=analysis.frame_id,
        signals=analysis.payload,
        events=persisted_events,
        evidence_asset=evidence_asset,
    )


@router.post("/{session_id}/analyze-audio", response_model=AudioAnalysisResponse)
def analyze_audio(
    session_id: int,
    sample_rate: int = Form(44100),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_request_settings),
    analyzer: PCM16AudioAnalyzer = Depends(get_audio_analyzer),
) -> AudioAnalysisResponse:
    session = _get_owned_session(db, session_id, current_user)
    content = file.file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Audio upload is empty")

    signals = analyzer.signals(content, sample_rate)
    detector_events = analyzer.analyze(content, sample_rate)
    should_store_evidence = any(
        policy.should_attach_evidence(event.event_type, event.confidence or 0.0)
        for event in detector_events
    )

    evidence_asset = None
    if should_store_evidence:
        evidence_asset = _save_evidence_asset(
            db,
            settings,
            session,
            file.filename or "audio.pcm",
            file.content_type,
            content,
        )

    persisted_events = [
        _persist_detector_event(db, session, detector_event, evidence_asset)
        for detector_event in detector_events
    ]
    db.commit()
    for event in persisted_events:
        db.refresh(event)
    if evidence_asset is not None:
        db.refresh(evidence_asset)

    return AudioAnalysisResponse(signals=signals, events=persisted_events, evidence_asset=evidence_asset)
