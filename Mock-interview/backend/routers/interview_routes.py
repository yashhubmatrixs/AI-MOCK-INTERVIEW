import os
import shutil
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

import models
import schemas
from auth import get_current_user
from database import get_db
from services import resume_parser, llm_service, stt_service, question_bank_service, grounding_service

router = APIRouter(prefix="/interviews", tags=["interviews"])

AUDIO_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads", "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)


def _get_owned_interview(interview_id: int, db: Session, current_user: models.User) -> models.Interview:
    interview = db.query(models.Interview).filter(models.Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found.")
    if interview.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your interview.")
    return interview


@router.post("/", response_model=schemas.InterviewDetailOut)
def create_interview(
    company_name: str = Form(...),
    job_title: str = Form(...),
    job_description: str = Form(...),
    num_questions: int = Form(6),
    resume: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    resume_bytes = resume.file.read()
    try:
        resume_text = resume_parser.extract_text_from_file(resume_bytes, resume.filename)
    except resume_parser.ResumeParseError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # Generate the questions BEFORE saving anything: if the model is down or out of
    # credit this raises (shown to the user as a 503) and no empty interview is left
    # behind in the database.
    seed_questions = question_bank_service.get_seed_questions(company_name, limit=20)
    planned = grounding_service.plan_questions(
        resume_text=resume_text,
        job_description=job_description,
        company_name=company_name,
        seed_questions=seed_questions,
        num_questions=num_questions,
    )

    interview = models.Interview(
        user_id=current_user.id,
        company_name=company_name,
        job_title=job_title,
        job_description=job_description,
        resume_filename=resume.filename,
        resume_text=resume_text,
        status="in_progress",
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)

    for i, q in enumerate(planned):
        db.add(
            models.Question(
                interview_id=interview.id,
                question_text=q["question_text"],
                question_type=q["question_type"],
                order_index=i,
                source=q["source"],
                evidence=[models.Evidence(**e) for e in q["evidence"]],
            )
        )
    db.commit()
    db.refresh(interview)
    return interview


@router.get("/", response_model=list[schemas.InterviewOut])
def list_interviews(
    db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    return (
        db.query(models.Interview)
        .filter(models.Interview.user_id == current_user.id)
        .order_by(models.Interview.created_at.desc())
        .all()
    )


@router.get("/{interview_id}", response_model=schemas.InterviewDetailOut)
def get_interview(
    interview_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return _get_owned_interview(interview_id, db, current_user)


@router.post("/{interview_id}/answers", response_model=schemas.AnswerOut)
def submit_answer(
    interview_id: int,
    question_id: int = Form(...),
    answer_text: str | None = Form(None),
    audio: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    interview = _get_owned_interview(interview_id, db, current_user)
    question = (
        db.query(models.Question)
        .filter(models.Question.id == question_id, models.Question.interview_id == interview.id)
        .first()
    )
    if not question:
        raise HTTPException(status_code=404, detail="Question not found on this interview.")

    audio_path = None
    final_text = answer_text or ""

    if audio is not None:
        ext = os.path.splitext(audio.filename or "answer.webm")[1] or ".webm"
        audio_path = os.path.join(AUDIO_DIR, f"{uuid.uuid4().hex}{ext}")
        with open(audio_path, "wb") as f:
            shutil.copyfileobj(audio.file, f)
        try:
            final_text = stt_service.transcribe_audio(audio_path)
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Transcription failed: {exc}")

    evaluation = grounding_service.grade_answer(
        question_text=question.question_text,
        question_type=question.question_type,
        answer_text=final_text,
        job_description=interview.job_description,
    )

    existing = db.query(models.Answer).filter(models.Answer.question_id == question.id).first()
    if existing:
        answer = existing
    else:
        answer = models.Answer(question_id=question.id)
        db.add(answer)

    answer.answer_text = final_text
    answer.audio_path = audio_path or answer.audio_path
    answer.score = evaluation["score"]
    answer.feedback = evaluation["feedback"]
    answer.strengths = evaluation["strengths"]
    answer.weaknesses = evaluation["weaknesses"]

    # Replace (not append to) the sources when an answer is re-submitted.
    for old in list(answer.evidence):
        db.delete(old)
    answer.evidence = [models.Evidence(**e) for e in evaluation["evidence"]]

    db.commit()
    db.refresh(answer)
    return answer


@router.post("/{interview_id}/complete", response_model=schemas.ReportOut)
def complete_interview(
    interview_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    from datetime import datetime

    interview = _get_owned_interview(interview_id, db, current_user)
    questions = (
        db.query(models.Question)
        .filter(models.Question.interview_id == interview.id)
        .order_by(models.Question.order_index)
        .all()
    )

    qa_pairs = []
    for q in questions:
        qa_pairs.append(
            {
                "question": q.question_text,
                "question_type": q.question_type,
                "answer": q.answer.answer_text if q.answer else None,
                "score": q.answer.score if q.answer else None,
                "feedback": q.answer.feedback if q.answer else None,
            }
        )

    report = llm_service.generate_overall_report(qa_pairs)

    interview.status = "completed"
    interview.completed_at = datetime.utcnow()
    interview.overall_score = report["overall_score"]
    interview.positive_points = report["positive_points"]
    interview.negative_points = report["negative_points"]
    interview.summary = report["summary"]
    db.commit()
    db.refresh(interview)

    incident_count = (
        db.query(models.ProctoringEvent)
        .filter(models.ProctoringEvent.interview_id == interview.id)
        .count()
    )

    return schemas.ReportOut(
        interview=interview,
        positive_points=interview.positive_points or [],
        negative_points=interview.negative_points or [],
        summary=interview.summary,
        questions=questions,
        proctoring_incident_count=incident_count,
        proctoring_events=[],
    )
