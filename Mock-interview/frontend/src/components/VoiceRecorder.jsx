import { useState, useRef, useMemo } from "react";

// Records locally with MediaRecorder, then hands the finished blob to the
// parent via onChange - the parent uploads it once the candidate hits the
// shared "Submit answer" button, same as the text/code question types.
// Transcription happens server-side (Whisper) after upload, not live here.
export default function VoiceRecorder({ value, onChange }) {
  const [recording, setRecording] = useState(false);
  const [seconds, setSeconds] = useState(0);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const timerRef = useRef(null);

  const audioUrl = useMemo(() => (value ? URL.createObjectURL(value) : null), [value]);

  async function startRecording() {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const recorder = new MediaRecorder(stream);
    chunksRef.current = [];
    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunksRef.current.push(e.data);
    };
    recorder.onstop = () => {
      const blob = new Blob(chunksRef.current, { type: "audio/webm" });
      onChange(blob);
      stream.getTracks().forEach((t) => t.stop());
    };
    recorder.start();
    mediaRecorderRef.current = recorder;
    setRecording(true);
    setSeconds(0);
    timerRef.current = setInterval(() => setSeconds((s) => s + 1), 1000);
  }

  function stopRecording() {
    mediaRecorderRef.current?.stop();
    clearInterval(timerRef.current);
    setRecording(false);
  }

  function reRecord() {
    onChange(null);
  }

  const mm = String(Math.floor(seconds / 60)).padStart(2, "0");
  const ss = String(seconds % 60).padStart(2, "0");

  return (
    <div>
      <div className="recorder">
        <button
          type="button"
          className={`recorder__btn ${!recording ? "is-idle" : ""}`}
          onClick={recording ? stopRecording : startRecording}
          aria-label={recording ? "Stop recording" : "Start recording"}
        >
          {recording ? "\u25A0" : "\u25CF"}
        </button>
        <div>
          <div className="mono">
            {recording
              ? `Recording... ${mm}:${ss}`
              : value
              ? "Recording captured"
              : "Tap to answer out loud"}
          </div>
          <p style={{ margin: 0, fontSize: "0.8rem" }}>
            {recording
              ? "Tap again when you're done."
              : "Your answer is transcribed automatically after you submit."}
          </p>
        </div>
      </div>
      {value && !recording && (
        <div className="recorder__transcript">
          <audio controls src={audioUrl} style={{ width: "100%" }} />
          <div>
            <button type="button" className="btn btn-ghost" style={{ marginTop: 10 }} onClick={reRecord}>
              Re-record
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
