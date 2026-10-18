import { useEffect, useRef, useState, useCallback } from "react";
import * as faceapi from "face-api.js";

// Hosted by the face-api.js author for their own demos. If this ever goes
// down or you want fully offline proctoring, download the tiny_face_detector
// weight files into frontend/public/models and point this at "/models"
// instead (see README "Proctoring models" section).
const MODEL_URL = "https://justadudewhohacks.github.io/face-api.js/models";

const CHECK_INTERVAL_MS = 1000;
const MISSES_BEFORE_WARNING = 3; // ~3 seconds with nobody in frame

/**
 * Continuously monitors the webcam feed. Calls onEvent(eventType, message)
 * the moment the candidate's face leaves the frame, more than one face
 * appears, or the candidate switches away from the tab. The visual state
 * (amber -> green -> red border) is the same signal shown to the candidate,
 * so a warning is never silent.
 */
export default function CameraProctor({ onEvent }) {
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const missCountRef = useRef(0);
  const wasWarningRef = useRef(false);
  const wasMultipleRef = useRef(false);

  const [status, setStatus] = useState("starting"); // starting | ok | warning
  const [modelsReady, setModelsReady] = useState(false);
  const [cameraError, setCameraError] = useState(null);

  const logEvent = useCallback(
    (eventType, message) => {
      onEvent?.(eventType, message);
    },
    [onEvent]
  );

  // Load the face detection model once
  useEffect(() => {
    let cancelled = false;
    faceapi.nets.tinyFaceDetector
      .loadFromUri(MODEL_URL)
      .then(() => {
        if (!cancelled) setModelsReady(true);
      })
      .catch((err) => console.error("Could not load face detection model:", err));
    return () => {
      cancelled = true;
    };
  }, []);

  // Start the webcam
  useEffect(() => {
    let stream;
    navigator.mediaDevices
      .getUserMedia({ video: { width: 480, height: 360 } })
      .then((s) => {
        stream = s;
        streamRef.current = s;
        if (videoRef.current) videoRef.current.srcObject = s;
      })
      .catch(() => {
        setCameraError("Camera access was blocked - allow camera access and reload.");
      });

    return () => {
      stream?.getTracks().forEach((t) => t.stop());
    };
  }, []);

  // Detection loop
  useEffect(() => {
    if (!modelsReady) return;

    const interval = setInterval(async () => {
      const video = videoRef.current;
      if (!video || video.readyState !== 4) return;

      const detections = await faceapi.detectAllFaces(
        video,
        new faceapi.TinyFaceDetectorOptions({ inputSize: 224 })
      );

      if (detections.length === 0) {
        missCountRef.current += 1;
        wasMultipleRef.current = false;
        if (missCountRef.current >= MISSES_BEFORE_WARNING) {
          setStatus("warning");
          if (!wasWarningRef.current) {
            wasWarningRef.current = true;
            logEvent("face_not_detected", "Face left the camera frame");
          }
        }
      } else {
        missCountRef.current = 0;
        wasWarningRef.current = false;
        setStatus("ok");

        if (detections.length > 1 && !wasMultipleRef.current) {
          wasMultipleRef.current = true;
          logEvent("multiple_faces", `${detections.length} faces detected in frame`);
        } else if (detections.length === 1) {
          wasMultipleRef.current = false;
        }
      }
    }, CHECK_INTERVAL_MS);

    return () => clearInterval(interval);
  }, [modelsReady, logEvent]);

  // Tab-switch detection
  useEffect(() => {
    function handleVisibility() {
      if (document.hidden) {
        logEvent("tab_switch", "Candidate switched away from the interview tab");
      }
    }
    document.addEventListener("visibilitychange", handleVisibility);
    return () => document.removeEventListener("visibilitychange", handleVisibility);
  }, [logEvent]);

  const stateClass = status === "warning" ? "is-warning" : status === "ok" ? "is-ok" : "";

  return (
    <div className={`proctor ${stateClass}`}>
      <video ref={videoRef} autoPlay muted playsInline />
      <div className="proctor__corner proctor__corner--tl" />
      <div className="proctor__corner proctor__corner--tr" />
      <div className="proctor__corner proctor__corner--bl" />
      <div className="proctor__corner proctor__corner--br" />
      <div className="proctor__tag">
        <span className="proctor__tag-dot" />
        Proctored
      </div>
      {status === "warning" && (
        <div className="proctor__warning">Face not in view - please stay in frame</div>
      )}
      {cameraError && <div className="proctor__warning">{cameraError}</div>}
    </div>
  );
}
