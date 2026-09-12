import {
    useEffect,
    useRef,
    useState,
} from "react";

import { api } from "../lib/api";
import Icon from "../components/Icon";
import Topbar from "../components/Topbar";

export default function WorkerDashboard({
    user = {},
    onLogout,
}) {
    const workerName =
        user?.name ||
        user?.full_name ||
        user?.username ||
        "Worker";

    const workerInitial =
        workerName.trim().charAt(0).toUpperCase() || "W";

    const [data, setData] = useState({
        issues: [],
        machines: [],
    });

    const [active, setActive] = useState(null);
    const [text, setText] = useState("");
    const [messages, setMessages] = useState([]);
    const [busy, setBusy] = useState(false);
    const [recording, setRecording] = useState(false);
    const [machineId, setMachineId] = useState("");
    const [speaking, setSpeaking] = useState(null);

    const recorder = useRef(null);
    const chunks = useRef([]);

    // =========================================
    // LOAD DASHBOARD
    // =========================================

    async function refresh() {
        try {
            const result = await api.workerDashboard(
                user?.id
            );

            setData({
                issues: result || [],
                machines: await api.getMachines(),
            });
        } catch (error) {
            console.error(
                "Worker dashboard error:",
                error
            );

            setData({
                issues: [],
                machines: [],
            });
        }
    }

    useEffect(() => {
        refresh();
    }, []);

    const issueList = data?.issues || [];
    const machineList = data?.machines || [];

    // =========================================
    // SUBMIT TEXT ISSUE
    // =========================================

    async function submit(value = text) {
        if (!value?.trim() || busy) {
            return;
        }

        const content = value.trim();

        setText("");

        setMessages((previous) => [
            ...previous,
            {
                role: "user",
                content,
            },
        ]);

        setBusy(true);

        try {
            const response = await api.analyzeIssue(
                content,
                null,
                user?.id,
                machineId || null,
                active
            );

            const decision = response || {};

            setActive(
                response?.issue_id || active
            );

            setMessages((previous) => [
                ...previous,
                {
                    role: "ai",

                    content:
                        decision.worker_can_resolve
                            ? decision.troubleshooting_message ||
                              "Follow the safe troubleshooting steps."
                            : `${
                                decision.technician_message ||
                                decision.troubleshooting_message ||
                                "Technician intervention is required."
                            } ${
                                decision.technician_alert_sent
                                    ? "Technician call initiated."
                                    : "Technician call could not be initiated."
                            }`,

                    decision,
                },
            ]);

            await refresh();

        } catch (error) {
            console.error(
                "Issue analysis error:",
                error
            );

            setMessages((previous) => [
                ...previous,
                {
                    role: "error",
                    content:
                        error?.message ||
                        "Unable to analyze the issue.",
                },
            ]);
        } finally {
            setBusy(false);
        }
    }

    // =========================================
    // START VOICE
    // =========================================

    async function startVoice() {
        if (busy) {
            return;
        }

        try {
            const stream =
                await navigator.mediaDevices.getUserMedia({
                    audio: true,
                });

            const mediaRecorder =
                new MediaRecorder(stream);

            recorder.current = mediaRecorder;
            chunks.current = [];

            mediaRecorder.ondataavailable = (event) => {
                if (
                    event.data &&
                    event.data.size > 0
                ) {
                    chunks.current.push(event.data);
                }
            };

            mediaRecorder.onstop = async () => {
                stream
                    .getTracks()
                    .forEach((track) =>
                        track.stop()
                    );

                setRecording(false);

                if (!chunks.current.length) {
                    return;
                }

                setBusy(true);

                try {
                    const blob = new Blob(
                        chunks.current,
                        {
                            type: "audio/webm",
                        }
                    );

                    console.log(
                        "Voice recording:",
                        blob.size,
                        "bytes"
                    );

                    const response =
                        await api.analyzeVoice(
                            blob,
                            null,
                            user?.id,
                            machineId || null,
                            active
                        );

                    const decision =
                        response?.decision || {};

                    setActive(
                        response?.issue_id || active
                    );

                    setMessages((previous) => [
                        ...previous,

                        {
                            role: "user",
                            content:
                                response?.transcript ||
                                "Voice report",
                        },

                        {
                            role: "ai",

                            content:
                                decision
                                    ?.troubleshooting_message ||
                                decision
                                    ?.technician_message ||
                                "Issue escalated.",

                            decision,
                        },
                    ]);

                    await refresh();

                } catch (error) {
                    console.error(
                        "Voice analysis error:",
                        error
                    );

                    setMessages((previous) => [
                        ...previous,

                        {
                            role: "error",
                            content:
                                error?.message ||
                                "Unable to process voice report.",
                        },
                    ]);
                } finally {
                    setBusy(false);
                }
            };

            mediaRecorder.start();

            setRecording(true);

        } catch (error) {
            console.error(
                "Microphone error:",
                error
            );

            alert(
                "Microphone access was denied or is unavailable."
            );
        }
    }

    // =========================================
    // STOP VOICE
    // =========================================

    function stopVoice() {
        if (
            recorder.current &&
            recorder.current.state !== "inactive"
        ) {
            recorder.current.stop();
        }

        setRecording(false);
    }

    // =========================================
    // OPEN HISTORY ISSUE
    // =========================================

    function openIssue(issue) {
        setActive(issue?.id);

        setMachineId(issue?.machine_id || "");

        if (issue?.conversation?.length) {
            setMessages(
                issue.conversation.map((message) => ({
                    role: message.role,
                    content: message.content,
                    decision: message.decision,
                }))
            );
            return;
        }

        setMessages([
            {
                role: "user",
                content:
                    issue?.message ||
                    issue?.raised_issue_message ||
                    "Machine issue",
            },

            {
                role: "ai",

                content:
                    issue?.resolution ||
                    issue?.response_message ||
                    "This issue was escalated to the maintenance team.",

                decision: {
                    worker_can_resolve:
                        !!issue?.worker_can_resolve,

                    confidence:
                        Number(issue?.confidence) || 0,

                    technician_alert_sent:
                        !!issue?.technician_alert_sent,
                },
            },
        ]);
    }

    async function playReply(message, index) {
        if (!message?.content || speaking === index) {
            return;
        }

        setSpeaking(index);
        try {
            const audioBlob = await api.synthesizeSpeech(
                message.content,
                user?.language || "en-IN"
            );
            const audioUrl = URL.createObjectURL(audioBlob);
            const audio = new Audio(audioUrl);
            audio.onended = () => {
                URL.revokeObjectURL(audioUrl);
                setSpeaking(null);
            };
            audio.onerror = () => {
                URL.revokeObjectURL(audioUrl);
                setSpeaking(null);
            };
            await audio.play();
        } catch (error) {
            console.error("Speech playback error:", error);
            setSpeaking(null);
        }
    }

    // =========================================
    // RENDER
    // =========================================

    return (
        <div className="app-shell">

            {/* SIDEBAR */}

            <aside className="sidebar">

                <div className="side-brand">

                    <div className="brand-dot">
                        <Icon
                            name="shield"
                            size={20}
                        />
                    </div>

                    <div>
                        <b>AI Supervisor</b>

                        <small>
                            Worker Console
                        </small>
                    </div>

                </div>

                <button
                    className="new-chat"
                    type="button"
                    onClick={() => {
                        setMessages([]);
                        setActive(null);
                        setText("");
                        setMachineId("");
                    }}
                >
                    <Icon
                        name="plus"
                        size={18}
                    />

                    New report
                </button>

                <div className="history-title">

                    REPORTED ISSUES

                    <span>
                        {issueList.length}
                    </span>

                </div>

                <div className="history-list">

                    {issueList.map((issue) => (
                        <button
                            className={`history-item ${
                                active === issue?.id
                                    ? "active"
                                    : ""
                            }`}
                            key={issue?.id}
                            type="button"
                            onClick={() =>
                                openIssue(issue)
                            }
                        >

                            <Icon
                                name="chat"
                                size={16}
                            />

                            <div>

                                <b>
                                    {issue?.issue ||
                                        issue?.message ||
                                        issue?.raised_issue_message ||
                                        "Machine issue"}
                                </b>

                                <small>
                                    {issue?.created_at
                                        ? new Date(
                                              issue.created_at
                                          ).toLocaleString()
                                        : ""}
                                </small>

                            </div>

                        </button>
                    ))}

                    {!issueList.length && (
                        <div className="empty-history">
                            Your reported issues will
                            appear here.
                        </div>
                    )}

                </div>

                <div className="sidebar-footer">

                    <div className="status-dot" />

                    Session active

                </div>

            </aside>

            {/* MAIN */}

            <main className="main-panel">

                <Topbar
                    user={user}
                    onLogout={onLogout}
                    title="Worker workspace"
                    subtitle="Report a machine problem and get safe, manual-aware guidance."
                />

                <section className="worker-body">

                    {/* CHAT */}

                    <div className="chat-scroll">

                        {messages.length === 0 ? (

                            <div className="welcome">

                                <div className="welcome-icon">
                                    <Icon
                                        name="shield"
                                        size={32}
                                    />
                                </div>

                                <h2>
                                    How can I help
                                    with the machine?
                                </h2>

                                <p>
                                    Describe the symptom,
                                    alarm, sound, or machine
                                    behavior. I'll check
                                    the available manuals
                                    when needed.
                                </p>

                                <div className="suggestions">

                                    <button
                                        type="button"
                                        onClick={() =>
                                            setText(
                                                "The machine has stopped and is showing an alarm."
                                            )
                                        }
                                    >
                                        Machine stopped
                                        with an alarm
                                    </button>

                                    <button
                                        type="button"
                                        onClick={() =>
                                            setText(
                                                "The motor is making an unusual noise."
                                            )
                                        }
                                    >
                                        Motor making
                                        unusual noise
                                    </button>

                                    <button
                                        type="button"
                                        onClick={() =>
                                            setText(
                                                "The machine is not starting after reset."
                                            )
                                        }
                                    >
                                        Machine will
                                        not start
                                    </button>

                                </div>

                            </div>

                        ) : (

                            messages.map(
                                (message, index) => (

                                    <div
                                        key={index}
                                        className={`message-row ${
                                            message?.role || ""
                                        }`}
                                    >

                                        <div className="message-avatar">

                                            {message?.role ===
                                            "user"
                                                ? workerInitial
                                                : message?.role ===
                                                  "error"
                                                ? "!"
                                                : "AI"}

                                        </div>

                                        <div className="message-card">

                                            <div className="message-author">

                                                {message?.role ===
                                                "user"
                                                    ? workerName
                                                    : message?.role ===
                                                      "error"
                                                    ? "System"
                                                    : "Industrial Supervisor"}

                                            </div>

                                            <div className="message-text">

                                                {message?.content ||
                                                    ""}

                                            </div>

                                            {message?.role === "ai" && (
                                                <button
                                                    type="button"
                                                    className="message-speaker"
                                                    onClick={() =>
                                                        playReply(
                                                            message,
                                                            index
                                                        )
                                                    }
                                                    disabled={
                                                        speaking === index
                                                    }
                                                    title="Play reply"
                                                >
                                                    <Icon name="volume" size={15} />
                                                    {speaking === index
                                                        ? "Playing"
                                                        : "Play reply"}
                                                </button>
                                            )}

                                            {message?.decision && (
                                                <div className="decision">

                                                    <span
                                                        className={
                                                            message
                                                                .decision
                                                                ?.worker_can_resolve
                                                                ? "safe"
                                                                : "escalated"
                                                        }
                                                    >
                                                        {message
                                                            .decision
                                                            ?.worker_can_resolve
                                                            ? "Operator resolution"
                                                            : "Technician escalation"}
                                                    </span>

                                                    <span>
                                                        {Math.round(
                                                            (
                                                                Number(
                                                                    message
                                                                        .decision
                                                                        ?.confidence
                                                                ) ||
                                                                0
                                                            ) * 100
                                                        )}
                                                        % confidence
                                                    </span>

                                                </div>
                                            )}

                                        </div>

                                    </div>

                                )
                            )

                        )}

                    </div>

                    {/* COMPOSER */}

                    <div className="composer-wrap">

                        <div className="composer-meta">

                            <label>

                                Machine

                                <select
                                    value={machineId}
                                    onChange={(e) =>
                                        setMachineId(
                                            e.target.value
                                        )
                                    }
                                    disabled={busy}
                                >

                                    <option value="">
                                        Not specified
                                    </option>

                                    {machineList.map(
                                        (machine) => (
                                            <option
                                                key={
                                                    machine?.id
                                                }
                                                value={
                                                    machine?.id
                                                }
                                            >
                                                {machine?.name ||
                                                    "Machine"}

                                                {machine?.machine_code
                                                    ? ` · ${machine.machine_code}`
                                                    : machine?.model
                                                    ? ` · ${machine.model}`
                                                    : ""}
                                            </option>
                                        )
                                    )}

                                </select>

                            </label>

                            <span>
                                AI can make mistakes.
                                Follow machine safety
                                procedures.
                            </span>

                        </div>

                        <div className="composer">

                            <textarea
                                value={text}
                                onChange={(e) =>
                                    setText(
                                        e.target.value
                                    )
                                }
                                onKeyDown={(e) => {

                                    if (
                                        e.key ===
                                            "Enter" &&
                                        !e.shiftKey
                                    ) {
                                        e.preventDefault();
                                        submit();
                                    }

                                }}
                                placeholder="Report a machine issue…"
                                rows="1"
                                disabled={busy}
                            />

                            <button
                                type="button"
                                className={`icon-button ${
                                    recording
                                        ? "recording"
                                        : ""
                                }`}
                                onClick={
                                    recording
                                        ? stopVoice
                                        : startVoice
                                }
                                disabled={
                                    busy &&
                                    !recording
                                }
                                title={
                                    recording
                                        ? "Stop recording"
                                        : "Voice report"
                                }
                            >
                                <Icon name="mic" />
                            </button>

                            <button
                                type="button"
                                className="send-button"
                                disabled={
                                    !text.trim() ||
                                    busy
                                }
                                onClick={() =>
                                    submit()
                                }
                            >
                                <Icon
                                    name="send"
                                    size={17}
                                />
                            </button>

                        </div>

                    </div>

                </section>

            </main>

        </div>
    );
}