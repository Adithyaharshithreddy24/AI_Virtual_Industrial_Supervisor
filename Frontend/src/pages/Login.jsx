import { useState } from "react";

import Icon from "../components/Icon";
import { api } from "../lib/api";


export default function Login({
    onLogin,
}) {

    const [username, setUsername] =
        useState("");

    const [password, setPassword] =
        useState("");

    const [error, setError] =
        useState("");

    const [busy, setBusy] =
        useState(false);


    async function submit(e) {

        e.preventDefault();

        setError("");
        setBusy(true);


        try {

            const cleanUsername =
                username.trim().toLowerCase();


            if (!cleanUsername) {
                throw new Error(
                    "Please enter your username."
                );
            }


            if (!password) {
                throw new Error(
                    "Please enter your password."
                );
            }


            const response =
                await api.login(
                    cleanUsername,
                    password
                );


            console.log(
                "LOGIN SUCCESS:",
                response.user
            );


            // -----------------------------------------
            // STORE AUTH TOKEN
            // -----------------------------------------

            localStorage.setItem(
                "access_token",
                response.access_token
            );


            // -----------------------------------------
            // STORE USER
            // -----------------------------------------

            localStorage.setItem(
                "user",
                JSON.stringify(
                    response.user
                )
            );


            // -----------------------------------------
            // SEND USER TO APP
            // -----------------------------------------

            onLogin(
                response.user
            );


        } catch (error) {

            console.error(
                "LOGIN ERROR:",
                error
            );


            setError(
                error.message ||
                "Unable to sign in."
            );

        } finally {

            setBusy(false);
        }
    }


    return (

        <div className="login-shell">


            {/* =====================================
                LEFT VISUAL PANEL
            ====================================== */}

            <div className="login-visual">

                <div className="brand-mark">

                    <Icon
                        name="shield"
                        size={30}
                    />

                </div>


                <div className="eyebrow">
                    AI INDUSTRIAL SUPERVISOR
                </div>


                <h1>

                    Safer decisions.

                    <br />

                    <span>
                        Faster maintenance.
                    </span>

                </h1>


                <p>
                    One operational workspace for
                    workers, managers and maintenance
                    teams.
                </p>


                <div className="login-feature">

                    <Icon name="machine" />

                    <span>
                        Manual-aware troubleshooting
                    </span>

                </div>


                <div className="login-feature">

                    <Icon name="alert" />

                    <span>
                        Instant technician escalation
                    </span>

                </div>

            </div>


            {/* =====================================
                LOGIN CARD
            ====================================== */}

            <div className="login-card">

                <div className="mobile-brand">
                    AI Industrial Supervisor
                </div>


                <h2>
                    Welcome back
                </h2>


                <p>
                    Sign in to continue to your
                    workspace.
                </p>


                <form
                    onSubmit={submit}
                >


                    {/* USERNAME */}

                    <label>

                        Username

                        <input
                            type="text"
                            value={username}
                            onChange={(e) =>
                                setUsername(
                                    e.target.value
                                )
                            }
                            autoComplete="username"
                            placeholder="Enter username"
                            required
                        />

                    </label>


                    {/* PASSWORD */}

                    <label>

                        Password

                        <input
                            type="password"
                            value={password}
                            onChange={(e) =>
                                setPassword(
                                    e.target.value
                                )
                            }
                            autoComplete="current-password"
                            placeholder="Enter password"
                            required
                        />

                    </label>


                    {/* ERROR */}

                    {error && (

                        <div className="error-box">

                            {error}

                        </div>

                    )}


                    {/* LOGIN */}

                    <button
                        type="submit"
                        className="primary-button"
                        disabled={busy}
                    >

                        {busy
                            ? "Signing in…"
                            : "Sign in"}

                        <span>
                            →
                        </span>

                    </button>


                </form>


                <div className="demo-box">

                    <b>
                        Database authentication
                    </b>

                    <span>
                        Sign in using an account
                        created in MongoDB.
                    </span>

                </div>


            </div>

        </div>
    );
}