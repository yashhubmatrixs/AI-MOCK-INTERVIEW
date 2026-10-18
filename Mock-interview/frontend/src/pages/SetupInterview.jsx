import { useState } from "react";
import { useNavigate } from "react-router-dom";
import client from "../api/client.js";

const COMPANY_SUGGESTIONS = ["Zensar", "TCS", "Infosys", "Wipro", "Accenture", "Amazon", "Google"];

export default function SetupInterview() {
  const navigate = useNavigate();
  const [companyName, setCompanyName] = useState("");
  const [jobTitle, setJobTitle] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [resumeFile, setResumeFile] = useState(null);
  const [numQuestions, setNumQuestions] = useState(6);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!resumeFile) {
      setError("Please attach your resume (PDF, DOCX or TXT).");
      return;
    }
    setError(null);
    setLoading(true);

    const form = new FormData();
    form.append("company_name", companyName);
    form.append("job_title", jobTitle);
    form.append("job_description", jobDescription);
    form.append("num_questions", numQuestions);
    form.append("resume", resumeFile);

    try {
      const { data } = await client.post("/interviews/", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      navigate(`/interview/${data.id}`);
    } catch (err) {
      setError(err.response?.data?.detail || "Could not start the interview. Try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page-narrow">
      <span className="eyebrow">New mock interview</span>
      <h1>Set up your interview</h1>
      <p>Your questions are generated from your resume, the job description, and the company you pick.</p>

      <form onSubmit={handleSubmit} className="card">
        <div className="field">
          <label>Company</label>
          <input
            type="text"
            list="company-suggestions"
            required
            placeholder="e.g. Zensar"
            value={companyName}
            onChange={(e) => setCompanyName(e.target.value)}
          />
          <datalist id="company-suggestions">
            {COMPANY_SUGGESTIONS.map((c) => (
              <option key={c} value={c} />
            ))}
          </datalist>
        </div>

        <div className="field">
          <label>Job title / role</label>
          <input
            type="text"
            required
            placeholder="e.g. GET Intern"
            value={jobTitle}
            onChange={(e) => setJobTitle(e.target.value)}
          />
        </div>

        <div className="field">
          <label>Job description</label>
          <textarea
            required
            placeholder="Paste the job description here"
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
          />
        </div>

        <div className="field">
          <label>Resume (PDF, DOCX or TXT)</label>
          <div className="file-drop">
            <input
              type="file"
              accept=".pdf,.docx,.txt"
              onChange={(e) => setResumeFile(e.target.files[0])}
            />
            {resumeFile && <p style={{ margin: "8px 0 0" }}>{resumeFile.name}</p>}
          </div>
        </div>

        <div className="field">
          <label>Number of questions</label>
          <select value={numQuestions} onChange={(e) => setNumQuestions(Number(e.target.value))}>
            <option value={4}>4 - quick round</option>
            <option value={6}>6 - standard</option>
            <option value={8}>8 - thorough</option>
          </select>
        </div>

        {error && <p className="error-text">{error}</p>}

        <button type="submit" className="btn btn-primary btn-block" disabled={loading}>
          {loading ? "Generating your questions..." : "Start interview"}
        </button>
      </form>
    </div>
  );
}
