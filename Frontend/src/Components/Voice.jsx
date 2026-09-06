import { useState, useEffect, useRef } from "react";
import "../Styles/Voice.css";

function VoiceRecorder() {
    const BACKEND_URL = import.meta.env.VITE_BACKEND_URL;

    const [isRecording, setIsRecording] = useState(false);
    const [seconds, setSeconds] = useState(0);
    const [status, setStatus] = useState("Ready to record");

    const mediaRecorderRef = useRef(null);
    const audioChunksRef = useRef([]);

    useEffect(() => {
        let timer;

        if (isRecording) {
            timer = setInterval(() => {
                setSeconds((prev) => prev + 1);
            }, 1000);
        }

        return () => clearInterval(timer);
    }, [isRecording]);

    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: true,
            });

            const mediaRecorder = new MediaRecorder(stream);

            mediaRecorderRef.current = mediaRecorder;
            audioChunksRef.current = [];

            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    audioChunksRef.current.push(event.data);
                }
            };

            mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(audioChunksRef.current, {
                    type: "audio/webm",
                });

                // Stop microphone
                stream.getTracks().forEach((track) => track.stop());

                console.log("Audio recorded:", audioBlob);

                // Send audio to FastAPI
                await sendAudioToBackend(audioBlob);
            };

            mediaRecorder.start();

            setSeconds(0);
            setIsRecording(true);
            setStatus("Recording...");

            console.log("Recording started");
        } catch (error) {
            console.error("Microphone error:", error);
            setStatus("Microphone access denied");
        }
    };

    const stopRecording = () => {
        if (
            mediaRecorderRef.current &&
            mediaRecorderRef.current.state !== "inactive"
        ) {
            mediaRecorderRef.current.stop();
        }

        setIsRecording(false);
        setStatus("Processing...");

        console.log("Recording stopped");
    };

    const sendAudioToBackend = async (audioBlob) => {
        try {
            const formData = new FormData();

            formData.append("file", audioBlob, "recording.webm");

            const response = await fetch(`${BACKEND_URL}/transcribe`, {
                method: "POST",
                body: formData,
            });

            if (!response.ok) {
                throw new Error("Backend request failed");
            }

            const responseJson = await response.json();

            console.log("Backend response:", responseJson);

            setStatus("Transcription is : " + responseJson.data);
        } catch (error) {
            console.error("Backend error:", error);
            setStatus("Backend connection failed");
        }
    };

    const toggleRecording = () => {
        if (isRecording) {
            stopRecording();
        } else {
            startRecording();
        }
    };

    const formatTime = (totalSeconds) => {
        const minutes = Math.floor(totalSeconds / 60)
            .toString()
            .padStart(2, "0");

        const secs = (totalSeconds % 60)
            .toString()
            .padStart(2, "0");

        return `${minutes}:${secs}`;
    };

    return (
        <div className="app">
            <div className="recorder-card">

                <div className={`mic-icon ${isRecording ? "recording" : ""}`}>
                    🎙️
                </div>

                <h1>Voice Recorder</h1>

                <p className="description">
                    Record your voice and convert it to text using Whisper.
                </p>

                <div className="timer">
                    {formatTime(seconds)}
                </div>

                <div className="status">
                    <span
                        className={`status-dot ${
                            isRecording ? "active" : ""
                        }`}
                    />

                    {status}
                </div>

                <button
                    className={`record-button ${
                        isRecording ? "stop" : ""
                    }`}
                    onClick={toggleRecording}
                >
                    {isRecording
                        ? "■ Stop Recording"
                        : "● Start Recording"}
                </button>

                {isRecording && (
                    <div className="recording-message">
                        Speak clearly into your microphone
                    </div>
                )}

                {!isRecording && seconds > 0 && (
                    <div className="recording-message">
                        Recording stopped — ready for transcription
                    </div>
                )}

            </div>
        </div>
    );
}

export default VoiceRecorder;