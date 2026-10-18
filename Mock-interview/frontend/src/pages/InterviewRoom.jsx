import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import client from "../api/client.js";
import CameraProctor from "../components/CameraProctor.jsx";
import QuestionCard from "../components/QuestionCard.jsx";
import Timer from "../components/Timer.jsx";
import { AnswerSources } from "../components/Sources.jsx";

const TIME_PER_TYPE = { essay: 180, code: 300, verbal: 120 };

export default function InterviewRoom() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [interview, setInterview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [index, setIndex] = useState(0);
  const [answerText, setAnswerText] = useState("");
  const [audioBlob, setAudioBlob] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [lastResult, setLastResult] = useState(null);
  const [proctorLog, setProctorLog] = useState([]);
  const [finishing, setFinishing] = useState(false);

  useEffect(() => {
    client
      .get(`/interviews/${id}`)
      .then(({ data }) => setInterview(data))
      .catch(() => setError("Could not load this interview."))
      .finally(() => setLoading(false));
  }, [id]);

  const handleProctorEvent = useCallback(
    (eventType, message) => {
      setProctorLog((log) => [...log.slice(-4), message]);
      client.post(`/interviews/${id}/proctoring-events`, { event_type: eventType, message }).catch(() => {});
    },
    [id]
  );

  if (loading) return <div className="page">Loading interview...</div>;
  if (error) return <div className="page error-text">{error}</div>;
  if (!interview || interview.questions.length === 0) {
    return <div className="page">This interview has no questions yet.</div>;
  }

  const question = interview.questions[index];
  const total = interview.questions.length;
  const isLast = index === total - 1;

  async function submitAnswer() {
    setSubmitting(true);
    const form = new FormData();
    form.append("question_id", question.id);
    if (question.question_type === "verbal" && audioBlob) {
      form.append("audio", audioBlob, "answer.webm");
    } else {
      form.append("answer_text", answerText);
    }

    try {
      const { data } = await client.post(`/interviews/${id}/answers`, form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setLastResult(data);
    } catch (err) {
      setError(err.response?.data?.detail || "Could not submit that answer.");
    } finally {
      setSubmitting(false);
    }
  }

  async function goNext() {
    if (isLast) {
      setFinishing(true);
      try {
        await client.post(`/interviews/${id}/complete`);
        navigate(`/report/${id}`);
      } catch {
        setError("Could not finalize the report. Your answers are saved - try again.");
        setFinishing(false);
      }
      return;
    }
    setIndex((i) => i + 1);
    setAnswerText("");
    setAudioBlob(null);
    setLastResult(null);
  }

  return (
    <div className="page">
      <div className="stepper">
        {interview.questions.map((q, i) => (
          <div
            key={q.id}
            className={`stepper__dot ${i < index ? "is-done" : i === index ? "is-current" : ""}`}
          />
        ))}
      </div>

      <div className="interview-grid">
        <div>
          <QuestionCard
            question={question}
            index={index}
            total={total}
            answerText={answerText}
            onAnswerTextChange={setAnswerText}
            audioBlob={audioBlob}
            onAudioChange={setAudioBlob}
          />

          {lastResult && (
            <div className="card">
              <h3>
                Score:{" "}
                <span className={lastResult.score >= 6 ? "mono" : "mono error-text"}>
                  {lastResult.score?.toFixed(1)}/10
                </span>
              </h3>
              <p>{lastResult.feedback}</p>
              <AnswerSources answer={lastResult} />
            </div>
          )}

          {error && <p className="error-text">{error}</p>}

          <div style={{ marginTop: 16, display: "flex", gap: 12 }}>
            {!lastResult ? (
              <button className="btn btn-primary" onClick={submitAnswer} disabled={submitting}>
                {submitting ? "Evaluating..." : "Submit answer"}
              </button>
            ) : (
              <button className="btn btn-primary" onClick={goNext} disabled={finishing}>
                {finishing ? "Generating report..." : isLast ? "Finish interview" : "Next question"}
              </button>
            )}
          </div>
        </div>

        <div className="rail">
          <CameraProctor onEvent={handleProctorEvent} />
          <Timer seconds={TIME_PER_TYPE[question.question_type] || 180} resetKey={question.id} />
          {proctorLog.length > 0 && (
            <div className="card">
              <h3>Proctoring log</h3>
              {proctorLog.map((m, i) => (
                <div key={i} className="proctor-log">
                  {m}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
