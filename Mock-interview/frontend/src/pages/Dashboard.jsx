import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import client from "../api/client.js";
import { useAuth } from "../context/AuthContext.jsx";

export default function Dashboard() {
  const { user } = useAuth();
  const [interviews, setInterviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");

  useEffect(() => {
    client
      .get("/interviews/")
      .then(({ data }) => setInterviews(data))
      .catch((err) => {
        // A 401 is handled globally (back to the login page); anything else is shown.
        if (err.response?.status !== 401) {
          setLoadError("Couldn't load your interviews. Is the backend running?");
        }
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="page">
      <span className="eyebrow">Dashboard</span>
      <h1>{user ? `Welcome back, ${user.full_name.split(" ")[0]}` : "Your interviews"}</h1>

      <div style={{ marginBottom: 20 }}>
        <Link to="/new" className="btn btn-primary">
          Start a new mock interview
        </Link>
      </div>

      {loading ? (
        <p>Loading...</p>
      ) : loadError ? (
        <div className="card empty-state">
          <p>{loadError}</p>
        </div>
      ) : interviews.length === 0 ? (
        <div className="card empty-state">
          <p>No interviews yet. Upload a resume and job description to generate your first one.</p>
        </div>
      ) : (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Company</th>
                <th>Role</th>
                <th>Status</th>
                <th>Score</th>
                <th>Date</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {interviews.map((iv) => (
                <tr key={iv.id}>
                  <td>{iv.company_name}</td>
                  <td>{iv.job_title}</td>
                  <td>
                    <span className={`status-pill ${iv.status}`}>{iv.status.replace("_", " ")}</span>
                  </td>
                  <td className="mono">{iv.overall_score != null ? iv.overall_score.toFixed(1) : "-"}</td>
                  <td>{new Date(iv.created_at).toLocaleDateString()}</td>
                  <td>
                    {iv.status === "completed" ? (
                      <Link to={`/report/${iv.id}`}>View report</Link>
                    ) : (
                      <Link to={`/interview/${iv.id}`}>Resume</Link>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
