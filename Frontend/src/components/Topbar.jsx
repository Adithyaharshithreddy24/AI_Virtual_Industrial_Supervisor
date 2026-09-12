import Icon from "./Icon";

export default function Topbar({
    user = {},
    onLogout,
    title = "Dashboard",
    subtitle = "",
}) {
    const name = user?.name || user?.username || "User";

    const initials = name
        .trim()
        .split(/\s+/)
        .filter(Boolean)
        .map((part) => part.charAt(0))
        .join("")
        .slice(0, 2)
        .toUpperCase() || "U";

    return (
        <header className="topbar">
            <div className="topbar-brand">
                <div className="topbar-logo">
                    <Icon name="shield" size={20} />
                </div>

                <div>
                    <strong>AI Industrial Supervisor</strong>
                    <span>Industrial operations</span>
                </div>
            </div>

            <div className="topbar-center">
                <h1>{title}</h1>
                {subtitle && <p>{subtitle}</p>}
            </div>

            <div className="topbar-user">
                <div className="user-avatar">
                    {initials}
                </div>

          

                <button
                    className="logout-button"
                    onClick={onLogout}
                    title="Logout"
                    type="button"
                >
                    <Icon name="logout" size={18} />
                </button>
            </div>
        </header>
    );
}