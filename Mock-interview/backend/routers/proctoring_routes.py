from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import models
import schemas
from auth import get_current_user
from database import get_db
from routers.interview_routes import _get_owned_interview

router = APIRouter(prefix="/interviews", tags=["proctoring"])


@router.post("/{interview_id}/proctoring-events")
def log_proctoring_event(
    interview_id: int,
    payload: schemas.ProctoringEventCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    interview = _get_owned_interview(interview_id, db, current_user)
    event = models.ProctoringEvent(
        interview_id=interview.id,
        event_type=payload.event_type,
        message=payload.message,
    )
    db.add(event)
    db.commit()
    return {"logged": True}


@router.get("/{interview_id}/proctoring-events")
def list_proctoring_events(
    interview_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    interview = _get_owned_interview(interview_id, db, current_user)
    events = (
        db.query(models.ProctoringEvent)
        .filter(models.ProctoringEvent.interview_id == interview.id)
        .order_by(models.ProctoringEvent.occurred_at)
        .all()
    )
    return [
        {
            "event_type": e.event_type,
            "message": e.message,
            "occurred_at": e.occurred_at.isoformat(),
        }
        for e in events
    ]
