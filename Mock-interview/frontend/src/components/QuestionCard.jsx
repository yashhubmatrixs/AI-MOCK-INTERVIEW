import CodeEditor from "./CodeEditor.jsx";
import VoiceRecorder from "./VoiceRecorder.jsx";
import { QuestionOrigin } from "./Sources.jsx";

const TYPE_LABEL = {
  essay: "Essay",
  code: "Code",
  verbal: "Verbal",
};

export default function QuestionCard({ question, index, total, answerText, onAnswerTextChange, audioBlob, onAudioChange }) {
  return (
    <div className="card">
      <span className={`badge badge-${question.question_type}`}>{TYPE_LABEL[question.question_type]}</span>
      <div className="question-number">
        Question {index + 1} of {total}
      </div>
      <h2 className="question-text">{question.question_text}</h2>
      <QuestionOrigin question={question} />

      <div style={{ marginTop: 20 }}>
        {question.question_type === "code" && (
          <CodeEditor value={answerText} onChange={onAnswerTextChange} />
        )}

        {question.question_type === "essay" && (
          <textarea
            className="code-editor"
            style={{ fontFamily: "var(--font-body)" }}
            placeholder="Write your answer here..."
            value={answerText}
            onChange={(e) => onAnswerTextChange(e.target.value)}
          />
        )}

        {question.question_type === "verbal" && (
          <VoiceRecorder value={audioBlob} onChange={onAudioChange} />
        )}
      </div>
    </div>
  );
}
