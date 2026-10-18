// Small, honest provenance labels: where a question came from, and what an
// answer's feedback was (or wasn't) checked against.

const ORIGIN_LABEL = {
  jd: "From the job description",
  resume: "From your resume",
  question_bank: "From the question bank",
  dsa_list: "From the DSA practice list",
  llm_generated: "General question - no source matched",
};

export function QuestionOrigin({ question }) {
  const label = ORIGIN_LABEL[question.source];
  if (!label) return null;
  const evidence = question.evidence?.[0];

  return (
    <div className="source-note">
      <span className={`source-chip ${question.source === "llm_generated" ? "is-unsourced" : ""}`}>{label}</span>
      {evidence && (
        <details className="source-details">
          <summary>Why this question</summary>
          <blockquote>
            <span className="source-ref">[{evidence.ref_id}]</span> {evidence.snippet}
          </blockquote>
        </details>
      )}
    </div>
  );
}

export function AnswerSources({ answer }) {
  if (!answer || answer.score == null) return null;

  if (!answer.grounded) {
    return (
      <p className="source-note source-warning">
        No reference notes matched this question, so technical accuracy was not checked against a
        source. Treat this score as feedback on structure and completeness.
      </p>
    );
  }

  return (
    <div className="source-note">
      <span className="source-chip">Reference notes consulted</span>
      <ul className="source-list">
        {answer.evidence.map((e) => (
          <li key={e.ref_id}>
            <details className="source-details">
              <summary>
                <span className="source-ref">[{e.ref_id}]</span> {e.source}
              </summary>
              <blockquote>{e.snippet}</blockquote>
            </details>
          </li>
        ))}
      </ul>
    </div>
  );
}
