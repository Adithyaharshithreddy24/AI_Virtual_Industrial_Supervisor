import { useEffect, useState } from "react";

import Icon from "../components/Icon";
import Topbar from "../components/Topbar";
import { api } from "../lib/api";
import "../styles/technician.css";

const STATUS_OPTIONS = [
    "yet to resolve",
    "technician alerted",
    "in progress",
    "resolved",
];

export default function TechnicianDashboard({
    user = {},
    onLogout,
}) {
    const [issues, setIssues] = useState([]);
    const [selectedId, setSelectedId] = useState(null);
    const [statusFilter, setStatusFilter] = useState("all");
    const [status, setStatus] = useState("yet to resolve");
    const [response, setResponse] = useState("");
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState("");

    async function refresh() {
        setLoading(true);
        try {
            const result = await api.technicianDashboard(user?.id);
            setIssues(result || []);
        } catch (error) {
            setMessage(error.message || "Unable to load assigned issues.");
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        refresh();
    }, []);

    const visibleIssues = issues.filter((issue) =>
        statusFilter === "all" || issue.status === statusFilter
    );

    const selectedIssue = issues.find(
        (issue) => issue.id === selectedId
    ) || visibleIssues[0] || null;

    useEffect(() => {
        if (!selectedIssue) {
            return;
        }

        setStatus(selectedIssue.status || "yet to resolve");
        setResponse(selectedIssue.response_message || "");
    }, [selectedIssue?.id]);

    function selectIssue(issue) {
        setSelectedId(issue.id);
        setStatus(issue.status || "yet to resolve");
        setResponse(issue.response_message || "");
        setMessage("");
    }

    async function saveIssue(event) {
        event.preventDefault();
        if (!selectedIssue || saving) {
            return;
        }

        setSaving(true);
        setMessage("");
        try {
            await api.updateIssue(
                selectedIssue.id,
                {
                    status,
                    response_message: response.trim() || null,
                },
                user?.id
            );
            setMessage("Issue updated successfully.");
            await refresh();
        } catch (error) {
            setMessage(error.message || "Unable to update issue.");
        } finally {
            setSaving(false);
        }
    }

    return (
        <div className="manager-shell">
            <Topbar
                user={user}
                onLogout={onLogout}
                title="Technician dashboard"
                subtitle="Review assigned issues and update maintenance progress."
            />

            <section className="manager-content">
                <div className="technician-toolbar">
                    <div>
                        <span className="eyebrow">ASSIGNED WORK</span>
                        <h2>{issues.length} assigned issues</h2>
                    </div>

                    <div className="technician-actions">
                        <select
                            value={statusFilter}
                            onChange={(event) =>
                                setStatusFilter(event.target.value)
                            }
                        >
                            <option value="all">All statuses</option>
                            {STATUS_OPTIONS.map((option) => (
                                <option key={option} value={option}>
                                    {option}
                                </option>
                            ))}
                        </select>
                        <button
                            className="outline-button"
                            type="button"
                            onClick={refresh}
                            disabled={loading}
                        >
                            <Icon name="refresh" />
                            Refresh
                        </button>
                    </div>
                </div>

                {message && <div className="toast">{message}</div>}

                {loading ? (
                    <div className="loading-state">
                        <div className="loading-spinner" />
                        <p>Loading assigned issues...</p>
                    </div>
                ) : (
                    <div className="technician-layout">
                        <div className="panel technician-issue-list">
                            <div className="panel-head">
                                <h3>Assigned issues</h3>
                            </div>
                            {visibleIssues.map((issue) => (
                                <button
                                    className={`technician-issue-item ${
                                        selectedIssue?.id === issue.id
                                            ? "active"
                                            : ""
                                    }`}
                                    key={issue.id}
                                    type="button"
                                    onClick={() => selectIssue(issue)}
                                >
                                    <strong>
                                        {issue.raised_issue_message}
                                    </strong>
                                    <small>
                                        {issue.status} · {new Date(
                                            issue.created_at
                                        ).toLocaleString()}
                                    </small>
                                </button>
                            ))}
                            {!visibleIssues.length && (
                                <div className="empty-history">
                                    No assigned issues match this filter.
                                </div>
                            )}
                        </div>

                        <div className="panel technician-detail">
                            <div className="panel-head">
                                <h3>Issue details</h3>
                            </div>
                            {selectedIssue ? (
                                <form onSubmit={saveIssue}>
                                    <div className="technician-detail-body">
                                        <span className="eyebrow">
                                            WORKER REPORT
                                        </span>
                                        <p className="technician-report">
                                            {selectedIssue.raised_issue_message}
                                        </p>

                                        <label>
                                            Status
                                            <select
                                                value={status}
                                                onChange={(event) =>
                                                    setStatus(event.target.value)
                                                }
                                            >
                                                {STATUS_OPTIONS.map((option) => (
                                                    <option
                                                        key={option}
                                                        value={option}
                                                    >
                                                        {option}
                                                    </option>
                                                ))}
                                            </select>
                                        </label>

                                        <label>
                                            Technician response
                                            <textarea
                                                rows="8"
                                                value={response}
                                                onChange={(event) =>
                                                    setResponse(event.target.value)
                                                }
                                                placeholder="Add inspection notes or resolution details"
                                            />
                                        </label>

                                        <button
                                            className="primary-button"
                                            type="submit"
                                            disabled={saving}
                                        >
                                            {saving ? "Saving..." : "Save update"}
                                            <span>→</span>
                                        </button>
                                    </div>
                                </form>
                            ) : (
                                <div className="empty-history">
                                    Select an assigned issue to update it.
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </section>
        </div>
    );
}
