import {
    useState,
} from "react";

import Login from "./pages/Login";
import WorkerDashboard from "./pages/WorkerDashboard";
import ManagerDashboard from "./pages/ManagerDashboard";
import TechnicianDashboard from "./pages/TechnicianDashboard";


function getStoredUser() {

    try {

        const storedUser =
            localStorage.getItem(
                "user"
            );


        if (!storedUser) {
            return null;
        }


        return JSON.parse(
            storedUser
        );

    } catch {

        localStorage.removeItem(
            "user"
        );

        localStorage.removeItem(
            "access_token"
        );

        return null;
    }
}


export default function App() {

    const [user, setUser] =
        useState(
            getStoredUser
        );


    function handleLogin(
        userData
    ) {

        console.log(
            "LOGIN SUCCESS:",
            userData
        );

        setUser(
            userData
        );
    }


    function handleLogout() {

        localStorage.removeItem(
            "access_token"
        );

        localStorage.removeItem(
            "user"
        );

        setUser(null);
    }


    // =================================================
    // LOGIN
    // =================================================

    if (!user) {

        return (
            <Login
                onLogin={
                    handleLogin
                }
            />
        );
    }


    // =================================================
    // MANAGER
    // =================================================

    if (
        user.role ===
        "manager"
    ) {

        return (
            <ManagerDashboard
                user={user}
                onLogout={
                    handleLogout
                }
            />
        );
    }

    if (user.role === "technician") {
        return (
            <TechnicianDashboard
                user={user}
                onLogout={handleLogout}
            />
        );
    }


    // =================================================
    // WORKER / TECHNICIAN
    // =================================================

    return (
        <WorkerDashboard
            user={user}
            onLogout={
                handleLogout
            }
        />
    );
}