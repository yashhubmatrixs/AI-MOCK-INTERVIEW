from datetime import datetime
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    ListFlowable,
    ListItem,
)

_SOURCE_LABEL = {
    "jd": "Based on the job description",
    "resume": "Based on your resume",
    "question_bank": "From the question bank",
    "dsa_list": "From the DSA practice list",
    "llm_generated": "General question (no source matched)",
}

GREEN = colors.HexColor("#1F7A5C")
RED = colors.HexColor("#B23A3A")
INK = colors.HexColor("#1A1E28")
GREY = colors.HexColor("#5B6273")


def generate_report_pdf(interview, questions_with_answers: list[dict], output_path: str):
    """interview: models.Interview instance.
    questions_with_answers: [{question_text, question_type, answer_text, score, feedback}, ...]
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleCustom", parent=styles["Title"], textColor=INK, fontSize=20
    )
    heading_style = ParagraphStyle(
        "HeadingCustom", parent=styles["Heading2"], textColor=INK, spaceBefore=14
    )
    body_style = ParagraphStyle("BodyCustom", parent=styles["BodyText"], textColor=INK)
    meta_style = ParagraphStyle("MetaCustom", parent=styles["BodyText"], textColor=GREY)

    story = []
    story.append(Paragraph("Mock Interview Report", title_style))
    story.append(Spacer(1, 6))
    story.append(
        Paragraph(
            f"{interview.company_name} &mdash; {interview.job_title}", meta_style
        )
    )
    date_str = (interview.completed_at or datetime.utcnow()).strftime("%d %b %Y, %H:%M")
    story.append(Paragraph(f"Completed: {date_str}", meta_style))
    story.append(Spacer(1, 16))

    score = interview.overall_score if interview.overall_score is not None else 0
    score_color = GREEN if score >= 6 else RED
    story.append(
        Paragraph(
            f'<font size="28" color="{score_color.hexval()}"><b>{score:.1f}/10</b></font> '
            f'<font size="12" color="{GREY.hexval()}">overall score</font>',
            body_style,
        )
    )
    story.append(Spacer(1, 10))

    if interview.summary:
        story.append(Paragraph(interview.summary, body_style))
        story.append(Spacer(1, 10))

    story.append(Paragraph("What went well", heading_style))
    positives = interview.positive_points or ["No standout strengths were recorded."]
    story.append(
        ListFlowable(
            [ListItem(Paragraph(p, body_style)) for p in positives],
            bulletColor=GREEN,
        )
    )

    story.append(Paragraph("Areas to improve", heading_style))
    negatives = interview.negative_points or ["No specific weaknesses were recorded."]
    story.append(
        ListFlowable(
            [ListItem(Paragraph(p, body_style)) for p in negatives],
            bulletColor=RED,
        )
    )

    story.append(Paragraph("Question-by-question breakdown", heading_style))
    note_style = ParagraphStyle(
        "NoteCustom", parent=body_style, textColor=GREY, fontSize=7.5, leading=9.5
    )
    table_data = [["#", "Type", "Score", "Question", "Feedback"]]
    for i, qa in enumerate(questions_with_answers, start=1):
        feedback_cell = [Paragraph(escape((qa.get("feedback") or "")[:220]), body_style)]
        if qa.get("answer_evidence"):
            names = ", ".join(
                dict.fromkeys(e["source"] for e in qa["answer_evidence"])
            )
            feedback_cell.append(Paragraph(escape(f"Checked against: {names}"), note_style))
        elif qa.get("score") is not None:
            feedback_cell.append(
                Paragraph("No reference found - technical accuracy was not checked.", note_style)
            )
        question_cell = [Paragraph(escape(qa.get("question_text", "")[:180]), body_style)]
        origin = _SOURCE_LABEL.get(qa.get("source") or "")
        if origin:
            question_cell.append(Paragraph(origin, note_style))
        table_data.append(
            [
                str(i),
                qa.get("question_type", ""),
                f"{qa['score']:.1f}" if qa.get("score") is not None else "-",
                question_cell,
                feedback_cell,
            ]
        )

    table = Table(table_data, colWidths=[1.1 * cm, 2 * cm, 1.6 * cm, 5.8 * cm, 6 * cm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), INK),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D8DBE3")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F6F8")]),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(table)

    doc.build(story)
    return output_path
