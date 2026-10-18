import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import client, { API_URL } from "../api/client.js";
import { QuestionOrigin, AnswerSources } from "../components/Sources.jsx";

export default function Report() {
  const { id } = useParams();
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    client
      .get(`/interviews/${id}/report`)
      .then(({ data }) => setReport(data))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="page">Loading report...</div>;
  if (!report) return <div className="page">Report not found.</div>;

  const score = report.interview.overall_score ?? 0;

  async function downloadPdf() {
    const token = localStorage.getItem("token");
    const res = await fetch(`${API_URL}/interviews/${id}/report/pdf`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `interview_${id}_report.pdf`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="page">
      <span className="eyebrow">
        {report.interview.company_name} &middot; {report.interview.job_title}
      </span>
      <h1>Interview report</h1>

      <div className="card" style={{ display: "flex", alignItems: "center", gap: 24 }}>
        <div className={`score-display ${score >= 6 ? "is-good" : "is-bad"}`}>{score.toFixed(1)}</div>
        <div>
          <p style={{ margin: 0 }}>out of 10 overall</p>
          {report.summary && <p style={{ marginTop: 8 }}>{report.summary}</p>}
        </div>
      </div>

      <div className="card">
        <h2>What went well</h2>
        <ul className="points-list positive">
          {report.positive_points.length > 0 ? (
            report.positive_points.map((p, i) => <li key={i}>{p}</li>)
          ) : (
            <li>No standout strengths recorded.</li>
          )}
        </ul>
      </div>

      <div className="card">
        <h2>Areas to improve</h2>
        <ul className="points-list negative">
          {report.negative_points.length > 0 ? (
            report.negative_points.map((p, i) => <li key={i}>{p}</li>)
          ) : (
            <li>No specific weaknesses recorded.</li>
          )}
        </ul>
      </div>

      {report.proctoring_incident_count > 0 && (
        <div className="card">
          <h2>Proctoring incidents</h2>
          <p>{report.proctoring_incident_count} event(s) were logged during this session.</p>
          {report.proctoring_events.map((e, i) => (
            <div key={i} className="proctor-log">
              {new Date(e.occurred_at).toLocaleTimeString()} - {e.message}
            </div>
          ))}
        </div>
      )}

      <div className="card">
        <h2>Question-by-question breakdown</h2>
        {report.questions.map((q, i) => (
          <div key={q.id} style={{ padding: "14px 0", borderBottom: "1px solid var(--line)" }}>
            <span className={`badge badge-${q.question_type}`}>{q.question_type}</span>
            <h3 style={{ marginTop: 8 }}>
              {i + 1}. {q.question_text}
            </h3>
            <QuestionOrigin question={q} />
            {q.answer ? (
              <>
                <p className="mono" style={{ color: "var(--paper)" }}>
                  Score: {q.answer.score?.toFixed(1) ?? "-"}/10
                </p>
                <p>{q.answer.feedback}</p>
                <AnswerSources answer={q.answer} />
              </>
            ) : (
              <p>Not answered.</p>
            )}
          </div>
        ))}
      </div>

      <div style={{ display: "flex", gap: 12, marginTop: 20 }}>
        <button className="btn btn-primary" onClick={downloadPdf}>
          Download PDF report
        </button>
        <Link to="/dashboard" className="btn btn-ghost">
          Back to dashboard
        </Link>
      </div>
    </div>
  );
}
