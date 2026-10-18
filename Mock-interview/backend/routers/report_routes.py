import os

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

import models
import schemas
from auth import get_current_user
from database import get_db
from routers.interview_routes import _get_owned_interview
from services import pdf_service

router = APIRouter(prefix="/interviews", tags=["report"])

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads", "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)


def _evidence_dicts(rows) -> list[dict]:
    return [
        {"kind": e.kind, "ref_id": e.ref_id, "source": e.source, "snippet": e.snippet}
        for e in rows
    ]


def _questions_with_answers(interview: models.Interview) -> list[dict]:
    result = []
    for q in interview.questions:
        result.append(
            {
                "question_text": q.question_text,
                "question_type": q.question_type,
                "source": q.source,
                "evidence": _evidence_dicts(q.evidence),
                "grounded": bool(q.answer and q.answer.evidence),
                "answer_evidence": _evidence_dicts(q.answer.evidence) if q.answer else [],
                "answer_text": q.answer.answer_text if q.answer else None,
                "score": q.answer.score if q.answer else None,
                "feedback": q.answer.feedback if q.answer else None,
                "strengths": q.answer.strengths if q.answer else [],
                "weaknesses": q.answer.weaknesses if q.answer else [],
            }
        )
    return result


@router.get("/{interview_id}/report", response_model=schemas.ReportOut)
def get_report(
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
    qwa = _questions_with_answers(interview)
    questions_out = []
    for q, qa in zip(interview.questions, qwa):
        questions_out.append(
            {
                "id": q.id,
                "question_text": q.question_text,
                "question_type": q.question_type,
                "order_index": q.order_index,
                "source": qa["source"],
                "evidence": qa["evidence"],
                "answer": (
                    {
                        "id": q.answer.id,
                        "question_id": q.id,
                        "answer_text": qa["answer_text"],
                        "score": qa["score"],
                        "feedback": qa["feedback"],
                        "strengths": qa["strengths"],
                        "weaknesses": qa["weaknesses"],
                        "grounded": qa["grounded"],
                        "evidence": qa["answer_evidence"],
                    }
                    if q.answer
                    else None
                ),
            }
        )

    return schemas.ReportOut(
        interview=interview,
        positive_points=interview.positive_points or [],
        negative_points=interview.negative_points or [],
        summary=interview.summary,
        questions=questions_out,
        proctoring_incident_count=len(events),
        proctoring_events=[
            {"event_type": e.event_type, "message": e.message, "occurred_at": e.occurred_at.isoformat()}
            for e in events
        ],
    )


@router.get("/{interview_id}/report/pdf")
def get_report_pdf(
    interview_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    interview = _get_owned_interview(interview_id, db, current_user)
    qwa = _questions_with_answers(interview)
    output_path = os.path.join(REPORTS_DIR, f"interview_{interview.id}_report.pdf")
    pdf_service.generate_report_pdf(interview, qwa, output_path)
    filename = f"{interview.company_name}_{interview.job_title}_report.pdf".replace(" ", "_")
    return FileResponse(output_path, media_type="application/pdf", filename=filename)
