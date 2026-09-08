import { useState } from "react";
import "../Styles/Calls.css";

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL;

function Calls() {
  const [phoneNumber, setPhoneNumber] = useState("");
  const [message, setMessage] = useState("");
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);

  const handleCall = async () => {
    if (!phoneNumber || !message) {
      setStatus("Please enter both phone number and message.");
      return;
    }

    setLoading(true);
    setStatus("");

    try {
      const response = await fetch(`${BACKEND_URL}/call`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: message,
          to_phone_number: phoneNumber,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Failed to make call");
      }

      if (data.success) {
        setStatus(
          `Call initiated successfully! Call SID: ${data.call_sid}`
        );
      } else {
        setStatus(`Call failed: ${data.message}`);
      }
    } catch (error) {
      setStatus(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="call-container">
      <h2>AI Industrial Supervisor</h2>

      <div className="form-group">
        <label htmlFor="phoneNumber">Phone Number</label>

        <input
          id="phoneNumber"
          type="tel"
          placeholder="+91XXXXXXXXXX"
          value={phoneNumber}
          onChange={(e) => setPhoneNumber(e.target.value)}
        />
      </div>

      <div className="form-group">
        <label htmlFor="message">Voice Message</label>

        <textarea
          id="message"
          placeholder="Enter the message to speak during the call..."
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          rows={5}
        />
      </div>

      <button
        className="call-button"
        onClick={handleCall}
        disabled={loading}
      >
        {loading ? "Calling..." : "📞 Call Technician"}
      </button>

      {status && <p className="status">{status}</p>}
    </div>
  );
}

export default Calls;
