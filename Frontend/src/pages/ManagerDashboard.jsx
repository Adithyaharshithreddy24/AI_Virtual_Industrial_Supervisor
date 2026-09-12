import {
    useEffect,
    useState,
} from "react";

import { api } from "../lib/api";
import Icon from "../components/Icon";
import Topbar from "../components/Topbar";


export default function ManagerDashboard({
    user,
    onLogout,
}) {

    // =====================================================
    // STATE
    // =====================================================

    const [data, setData] = useState({
        workers: [],
        machines: [],
        issues: [],
    });

    const [tab, setTab] =
        useState("overview");

    const [showMachine, setShowMachine] =
        useState(false);

    const [showWorker, setShowWorker] =
        useState(false);

    const [message, setMessage] =
        useState("");

    const [loading, setLoading] =
        useState(true);

    const [refreshing, setRefreshing] =
        useState(false);


    // =====================================================
    // LOAD DASHBOARD DATA
    // =====================================================

    async function refresh(
        showLoading = true
    ) {

        if (showLoading) {
            setLoading(true);
        } else {
            setRefreshing(true);
        }

        try {

            const [
                workers,
                machines,
                issues,
            ] = await Promise.all([
                api.getWorkers(),
                api.getMachines(),
                api.getIssues(),
            ]);


            setData({
                workers:
                    workers || [],

                machines:
                    machines || [],

                issues:
                    issues || [],
            });


            setMessage("");

        } catch (error) {

            console.error(
                "Manager dashboard error:",
                error
            );

            setMessage(
                error.message ||
                "Unable to load dashboard data."
            );

        } finally {

            setLoading(false);
            setRefreshing(false);
        }
    }


    // =====================================================
    // INITIAL LOAD
    // =====================================================

    useEffect(() => {
        refresh();
    }, []);


    // =====================================================
    // STATISTICS
    // =====================================================

    const workerCount =
        data.workers.length;

    const machineCount =
        data.machines.length;

    const issueCount =
        data.issues.length;

    const escalatedCount =
        data.issues.filter(
            (issue) =>
                issue.status ===
                "yet to resolve"
        ).length;

    const resolvedCount =
        data.issues.filter(
            (issue) =>
                issue.status ===
                "resolved"
        ).length;


    // =====================================================
    // ADD MACHINE
    // =====================================================

    async function addMachine(event) {

        event.preventDefault();

        const form =
            event.currentTarget;

        const formData =
            new FormData(form);


        try {

            setMessage(
                "Adding machine..."
            );


            await api.addMachine({
                name:
                    formData.get(
                        "name"
                    ),

                manufacturer:
                    formData.get(
                        "manufacturer"
                    ),

                model:
                    formData.get(
                        "model"
                    ),

                technician_id:
                    formData.get(
                        "technician_id"
                    ),

                user_manual:
                    formData.get(
                        "user_manual"
                    ),
            });


            form.reset();

            setShowMachine(false);

            setMessage(
                "Machine added successfully."
            );


            await refresh(false);

        } catch (error) {

            console.error(
                "Add machine error:",
                error
            );

            setMessage(
                error.message ||
                "Unable to add machine."
            );
        }
    }


    // =====================================================
    // ADD WORKER
    // =====================================================

    async function addWorker(event) {

        event.preventDefault();

        const form =
            event.currentTarget;

        const formData =
            new FormData(form);


        try {

            setMessage(
                "Creating account..."
            );


            await api.addWorker({
                name:
                    formData.get(
                        "name"
                    ),

                username:
                    formData.get(
                        "username"
                    ),

                password:
                    formData.get(
                        "password"
                    ),

                phone_number:
                    formData.get(
                        "phone_number"
                    ),

                role:
                    formData.get(
                        "role"
                    ) ||
                    "worker",

                language:
                    formData.get(
                        "language"
                    ) ||
                    "en-IN",
            });


            form.reset();

            setShowWorker(false);

            setMessage(
                "Account created successfully."
            );


            await refresh(false);

        } catch (error) {

            console.error(
                "Add worker error:",
                error
            );

            setMessage(
                error.message ||
                "Unable to create account."
            );
        }
    }


    // =====================================================
    // LOADING SCREEN
    // =====================================================

    if (loading) {

        return (
            <div className="manager-shell">

                <Topbar
                    user={user}
                    onLogout={onLogout}
                    title="Manager dashboard"
                    subtitle="Monitor operations, people, machines and maintenance events."
                />

                <div className="loading-state">

                    <div className="loading-spinner" />

                    <p>
                        Loading dashboard...
                    </p>

                </div>

            </div>
        );
    }


    // =====================================================
    // RENDER
    // =====================================================

    return (
        <div className="manager-shell">

            {/* =================================================
                TOPBAR
            ================================================== */}

            <Topbar
                user={user}
                onLogout={onLogout}
                title="Manager dashboard"
                subtitle="Monitor operations, people, machines and maintenance events."
            />


            {/* =================================================
                NAVIGATION
            ================================================== */}

            <div className="manager-nav">

                <button
                    className={
                        tab === "overview"
                            ? "active"
                            : ""
                    }
                    onClick={() =>
                        setTab(
                            "overview"
                        )
                    }
                >
                    Overview
                </button>


                <button
                    className={
                        tab === "issues"
                            ? "active"
                            : ""
                    }
                    onClick={() =>
                        setTab(
                            "issues"
                        )
                    }
                >
                    All issues
                </button>


                <button
                    className={
                        tab === "machines"
                            ? "active"
                            : ""
                    }
                    onClick={() =>
                        setTab(
                            "machines"
                        )
                    }
                >
                    Machines
                </button>


                <button
                    className={
                        tab === "workers"
                            ? "active"
                            : ""
                    }
                    onClick={() =>
                        setTab(
                            "workers"
                        )
                    }
                >
                    Workers
                </button>


                <div className="nav-spacer" />


                {/* REFRESH */}

                <button
                    className="outline-button"
                    onClick={() =>
                        refresh(false)
                    }
                    disabled={refreshing}
                >
                    <Icon name="refresh" />

                    {refreshing
                        ? "Refreshing..."
                        : "Refresh"}
                </button>


                {/* ADD MACHINE */}

                <button
                    className="outline-button"
                    onClick={() =>
                        setShowMachine(
                            true
                        )
                    }
                >
                    <Icon name="plus" />

                    Add machine
                </button>


                {/* ADD WORKER */}

                <button
                    className="outline-button"
                    onClick={() =>
                        setShowWorker(
                            true
                        )
                    }
                >
                    <Icon name="plus" />

                    Add worker
                </button>

            </div>


            {/* =================================================
                MESSAGE / TOAST
            ================================================== */}

            {message && (

                <div
                    className="toast"
                    onClick={() =>
                        setMessage("")
                    }
                >
                    {message}
                </div>

            )}


            {/* =================================================
                MAIN CONTENT
            ================================================== */}

            <section className="manager-content">


                {/* =================================================
                    OVERVIEW
                ================================================== */}

                {tab === "overview" && (

                    <>

                        {/* STATISTICS */}

                        <div className="stat-grid">

                            <Stat
                                icon="users"
                                label="Workers"
                                value={
                                    workerCount
                                }
                            />


                            <Stat
                                icon="machine"
                                label="Machines"
                                value={
                                    machineCount
                                }
                            />


                            <Stat
                                icon="chat"
                                label="Reported issues"
                                value={
                                    issueCount
                                }
                            />


                            <Stat
                                icon="alert"
                                label="Open escalations"
                                value={
                                    escalatedCount
                                }
                            />

                        </div>


                        {/* SECONDARY STATS */}

                        <div className="secondary-stat-grid">

                            <div className="mini-stat">

                                <span>
                                    Resolved issues
                                </span>

                                <strong>
                                    {
                                        resolvedCount
                                    }
                                </strong>

                            </div>


                            <div className="mini-stat">

                                <span>
                                    Open issues
                                </span>

                                <strong>
                                    {
                                        escalatedCount
                                    }
                                </strong>

                            </div>


                            <div className="mini-stat">

                                <span>
                                    Total issues
                                </span>

                                <strong>
                                    {
                                        issueCount
                                    }
                                </strong>

                            </div>

                        </div>


                        {/* DASHBOARD GRID */}

                        <div className="dashboard-grid">


                            {/* RECENT ISSUES */}

                            <Panel
                                title="Recent issues"
                                action={
                                    <button
                                        onClick={() =>
                                            setTab(
                                                "issues"
                                            )
                                        }
                                    >
                                        View all →
                                    </button>
                                }
                            >

                                <IssueTable
                                    issues={
                                        data.issues.slice(
                                            0,
                                            6
                                        )
                                    }
                                />

                            </Panel>


                            {/* MACHINE FLEET */}

                            <Panel
                                title="Machine fleet"
                                action={
                                    <button
                                        onClick={() =>
                                            setTab(
                                                "machines"
                                            )
                                        }
                                    >
                                        Manage →
                                    </button>
                                }
                            >

                                <MachineTable
                                    machines={
                                        data.machines.slice(
                                            0,
                                            6
                                        )
                                    }
                                />

                            </Panel>

                        </div>


                        {/* WORKERS */}

                        <Panel
                            title="Recent worker accounts"
                            action={
                                <button
                                    onClick={() =>
                                        setTab(
                                            "workers"
                                        )
                                    }
                                >
                                    View all →
                                </button>
                            }
                        >

                            <WorkerTable
                                workers={
                                    data.workers.slice(
                                        0,
                                        6
                                    )
                                }
                            />

                        </Panel>

                    </>
                )}


                {/* =================================================
                    ISSUES
                ================================================== */}

                {tab === "issues" && (

                    <Panel
                        title="All reported issues"
                        action={
                            <button
                                className="small-primary"
                                onClick={() =>
                                    refresh(
                                        false
                                    )
                                }
                            >
                                <Icon name="refresh" />

                                Refresh
                            </button>
                        }
                    >

                        <IssueTable
                            issues={
                                data.issues
                            }
                        />

                    </Panel>

                )}


                {/* =================================================
                    MACHINES
                ================================================== */}

                {tab === "machines" && (

                    <Panel
                        title="Machine fleet"
                        action={
                            <button
                                className="small-primary"
                                onClick={() =>
                                    setShowMachine(
                                        true
                                    )
                                }
                            >
                                <Icon name="plus" />

                                Add machine
                            </button>
                        }
                    >

                        <MachineTable
                            machines={
                                data.machines
                            }
                        />

                    </Panel>

                )}


                {/* =================================================
                    WORKERS
                ================================================== */}

                {tab === "workers" && (

                    <Panel
                        title="Worker accounts"
                        action={
                            <button
                                className="small-primary"
                                onClick={() =>
                                    setShowWorker(
                                        true
                                    )
                                }
                            >
                                <Icon name="plus" />

                                Add worker
                            </button>
                        }
                    >

                        <WorkerTable
                            workers={
                                data.workers
                            }
                        />

                    </Panel>

                )}

            </section>


            {/* =================================================
                ADD MACHINE MODAL
            ================================================== */}

            {showMachine && (

                <Modal
                    title="Add machine"
                    close={() =>
                        setShowMachine(
                            false
                        )
                    }
                >

                    <form
                        className="modal-form"
                        onSubmit={
                            addMachine
                        }
                    >

                        <label>
                            Machine name
                        </label>

                        <input
                            name="name"
                            placeholder="Machine name"
                            required
                        />


                        <label>
                            Manufacturer
                        </label>

                        <input
                            name="manufacturer"
                            placeholder="Manufacturer"
                            required
                        />


                        <label>
                            Model
                        </label>

                        <input
                            name="model"
                            placeholder="Model"
                            required
                        />


                        <label>
                            Assigned technician
                        </label>

                        <select
                            name="technician_id"
                            required
                            defaultValue=""
                        >

                            <option value="" disabled>
                                Choose a technician
                            </option>

                            {data.workers
                                .filter(
                                    (worker) =>
                                        worker.role ===
                                        "technician"
                                )
                                .map((technician) => (
                                    <option
                                        key={technician.id}
                                        value={technician.id}
                                    >
                                        {technician.name} · {technician.language || "en-IN"}
                                    </option>
                                ))}

                        </select>

                        {!data.workers.some(
                            (worker) =>
                                worker.role ===
                                "technician"
                        ) && (
                            <small className="form-help">
                                Add a technician account before creating a machine.
                            </small>
                        )}


                        <label>
                            User manual
                        </label>

                        <input
                            name="user_manual"
                            type="file"
                            accept="application/pdf"
                        />


                        <small className="form-help">
                            Upload the machine's
                            PDF user manual.
                        </small>


                        <button
                            className="primary-button"
                            type="submit"
                        >
                            Add machine

                            <span>
                                →
                            </span>
                        </button>

                    </form>

                </Modal>

            )}


            {/* =================================================
                ADD WORKER MODAL
            ================================================== */}

            {showWorker && (

                <Modal
                    title="Create account"
                    close={() =>
                        setShowWorker(
                            false
                        )
                    }
                >

                    <form
                        className="modal-form"
                        onSubmit={
                            addWorker
                        }
                    >

                        <label>
                            Full name
                        </label>

                        <input
                            name="name"
                            placeholder="Full name"
                            required
                        />


                        <label>
                            Username
                        </label>

                        <input
                            name="username"
                            placeholder="Username"
                            required
                        />


                        <label>
                            Password
                        </label>

                        <input
                            name="password"
                            type="password"
                            placeholder="Temporary password"
                            minLength="6"
                            required
                        />


                        <label>
                            Phone number
                        </label>

                        <input
                            name="phone_number"
                            type="tel"
                            placeholder="+91 9876543210"
                            required
                        />


                        <label>
                            Role
                        </label>

                        <select
                            name="role"
                            defaultValue="worker"
                            required
                        >

                            <option value="worker">
                                Worker
                            </option>

                            <option value="technician">
                                Technician
                            </option>

                        </select>


                        <label>
                            Language
                        </label>

                        <select
                            name="language"
                            defaultValue="en-IN"
                            required
                        >

                            <option value="en-IN">English</option>
                            <option value="hi-IN">Hindi</option>
                            <option value="bn-IN">Bengali</option>
                            <option value="gu-IN">Gujarati</option>
                            <option value="kn-IN">Kannada</option>
                            <option value="ml-IN">Malayalam</option>
                            <option value="mr-IN">Marathi</option>
                            <option value="od-IN">Odia</option>
                            <option value="pa-IN">Punjabi</option>
                            <option value="ta-IN">Tamil</option>
                            <option value="te-IN">Telugu</option>

                        </select>


                        <button
                            className="primary-button"
                            type="submit"
                        >
                            Create account

                            <span>
                                →
                            </span>
                        </button>

                    </form>

                </Modal>

            )}

        </div>
    );
}


/* =========================================================
   STAT CARD
========================================================= */

function Stat({
    icon,
    label,
    value,
}) {

    return (

        <div className="stat-card">

            <div className="stat-icon">

                <Icon name={icon} />

            </div>


            <div>

                <span>
                    {label}
                </span>

                <strong>
                    {value}
                </strong>

            </div>

        </div>
    );
}


/* =========================================================
   PANEL
========================================================= */

function Panel({
    title,
    action,
    children,
}) {

    return (

        <div className="panel">

            <div className="panel-head">

                <h3>
                    {title}
                </h3>

                {action}

            </div>


            {children}

        </div>
    );
}


/* =========================================================
   ISSUE TABLE
========================================================= */

function IssueTable({
    issues = [],
}) {

    return (

        <div className="table-wrap">

            <table>

                <thead>

                    <tr>

                        <th>
                            Issue
                        </th>

                        <th>
                            Worker
                        </th>

                        <th>
                            Machine
                        </th>

                        <th>
                            Status
                        </th>

                        <th>
                            Reported
                        </th>

                    </tr>

                </thead>


                <tbody>

                    {issues.map(
                        (issue) => (

                            <tr
                                key={
                                    issue.id
                                }
                            >

                                <td>

                                    <b>
                                        {
                                            issue.raised_issue_message ||
                                            "Unclassified issue"
                                        }
                                    </b>

                                    {issue.response_message && (

                                        <small>
                                            {
                                                issue.response_message
                                            }
                                        </small>

                                    )}

                                </td>


                                <td>

                                    {issue.worker_reported_id ||
                                        "—"}

                                </td>


                                <td>

                                    {issue.machine_id ||
                                        "—"}

                                </td>


                                <td>

                                    <StatusBadge
                                        status={
                                            issue.status
                                        }
                                    />

                                </td>


                                <td>

                                    {formatDate(
                                        issue.created_at
                                    )}

                                </td>

                            </tr>

                        )
                    )}


                    {!issues.length && (

                        <tr>

                            <td
                                colSpan="5"
                                className="empty-cell"
                            >
                                No issues reported yet.
                            </td>

                        </tr>

                    )}

                </tbody>

            </table>

        </div>
    );
}


/* =========================================================
   MACHINE TABLE
========================================================= */

function MachineTable({
    machines = [],
}) {

    return (

        <div className="table-wrap">

            <table>

                <thead>

                    <tr>

                        <th>
                            Machine
                        </th>

                        <th>
                            Manufacturer
                        </th>

                        <th>
                            Model
                        </th>

                        <th>
                            Manual
                        </th>

                    </tr>

                </thead>


                <tbody>

                    {machines.map(
                        (machine) => (

                            <tr
                                key={
                                    machine.id
                                }
                            >

                                <td>

                                    <b>
                                        {
                                            machine.name
                                        }
                                    </b>

                                </td>


                                <td>

                                    {
                                        machine.manufacturer ||
                                        "—"
                                    }

                                </td>


                                <td>

                                    {
                                        machine.model ||
                                        "—"
                                    }

                                </td>


                                <td>

                                    {machine.user_manual_file_id ? (

                                        <span className="badge ok">
                                            PDF available
                                        </span>

                                    ) : (

                                        <span className="badge">
                                            No manual
                                        </span>

                                    )}

                                </td>

                            </tr>

                        )
                    )}


                    {!machines.length && (

                        <tr>

                            <td
                                colSpan="4"
                                className="empty-cell"
                            >
                                No machines added.
                            </td>

                        </tr>

                    )}

                </tbody>

            </table>

        </div>
    );
}


/* =========================================================
   WORKER TABLE
========================================================= */

function WorkerTable({
    workers = [],
}) {

    return (

        <div className="table-wrap">

            <table>

                <thead>

                    <tr>

                        <th>
                            Name
                        </th>

                        <th>
                            Username
                        </th>

                        <th>
                            Phone
                        </th>

                        <th>
                            Role
                        </th>

                        <th>
                            Language
                        </th>

                    </tr>

                </thead>


                <tbody>

                    {workers.map(
                        (worker) => (

                            <tr
                                key={
                                    worker.id
                                }
                            >

                                <td>

                                    <b>
                                        {
                                            worker.name
                                        }
                                    </b>

                                </td>

                                <td>

                                    <code>
                                        {
                                            worker.username
                                        }
                                    </code>

                                </td>


                                <td>

                                    {
                                        worker.phone_number ||
                                        "—"
                                    }

                                </td>


                                <td>

                                    <span
                                        className={
                                            worker.role ===
                                            "technician"
                                                ? "badge warning"
                                                : "badge ok"
                                        }
                                    >
                                        {
                                            worker.role
                                        }
                                    </span>

                                </td>

                                <td>
                                    {worker.language || "en-IN"}
                                </td>

                            </tr>

                        )
                    )}


                    {!workers.length && (

                        <tr>

                            <td
                                colSpan="5"
                                className="empty-cell"
                            >
                                No workers added.
                            </td>

                        </tr>

                    )}

                </tbody>

            </table>

        </div>
    );
}


/* =========================================================
   STATUS BADGE
========================================================= */

function StatusBadge({
    status,
}) {

    const normalized =
        String(
            status || ""
        ).toLowerCase();


    if (
        normalized ===
        "resolved"
    ) {

        return (
            <span className="badge ok">
                Resolved
            </span>
        );
    }


    if (
        normalized ===
        "yet to resolve"
    ) {

        return (
            <span className="badge danger">
                Yet to resolve
            </span>
        );
    }


    return (
        <span className="badge">
            {status || "Unknown"}
        </span>
    );
}


/* =========================================================
   MODAL
========================================================= */

function Modal({
    title,
    close,
    children,
}) {

    return (

        <div
            className="modal-backdrop"
            onMouseDown={(event) => {

                if (
                    event.target ===
                    event.currentTarget
                ) {

                    close();
                }

            }}
        >

            <div className="modal">

                <div className="modal-head">

                    <h3>
                        {title}
                    </h3>


                    <button
                        type="button"
                        onClick={close}
                        aria-label="Close"
                    >
                        ×
                    </button>

                </div>


                {children}

            </div>

        </div>
    );
}


/* =========================================================
   DATE FORMATTER
========================================================= */

function formatDate(
    value
) {

    if (!value) {
        return "—";
    }


    const date =
        new Date(value);


    if (
        Number.isNaN(
            date.getTime()
        )
    ) {

        return "—";
    }


    return date.toLocaleString();
}