// npx create-react-app ai-ui
// cd ai-ui
// npm start

// Application restriction:
// → HTTP referrers (websites)

// Add:
// http://localhost:3000/*

import React, { useState, useEffect, useRef } from "react";
import MapView from "./MapView";
import DeleteMemoryButton from "./DeleteMemoryButton";

function App() {
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const chatEndRef = useRef(null);
  const eventSourceRef = useRef(null);

  useEffect(() => {
  const initializeSession = async () => {
    let storedSession = localStorage.getItem("session_id");
    if (!storedSession) {
      try {
        const res = await fetch("http://127.0.0.1:8000/api/get-session-id");
        const data = await res.json();
        storedSession = data.session_id;
        localStorage.setItem("session_id", storedSession);
      } catch (e) {
        console.error("Failed to fetch session ID", e);
        return;
      }
    }
    setSessionId(storedSession);
    console.log("Session ID:", storedSession);
  };

  initializeSession();
}, []);

//   useEffect(() => {
//   const fetchSession = async () => {
//     try {
//       // Example: fetch sessionId from backend
//       const res = await fetch("http://127.0.0.1:8000/api/get-session-id");
//       const data = await res.json();
//       setSessionId(data.session_id);
//       console.log("Session ID set to:", data.session_id);

//       // setSessionId("user3"); // MOCK: replace with real session logic
//       // console.log("Session ID set to:", sessionId);
//     } catch (e) {
//       console.error("Failed to get session id", e);
//     }
//   };

//   fetchSession();
// }, []);

  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // -------------------------------
  // Render Messages
  // -------------------------------
  const renderMessage = (msg, i) => {
    if (msg.role === "user") {
      return (
        <div key={i} style={{ margin: "10px 0" }}>
          <b>You:</b> {msg.text}
        </div>
      );
    }

    // -------------------------------
    // TEXT
    // -------------------------------
    if (msg.type === "message") {
      return (
        <div key={i} style={{ margin: "10px 0" }}>
          <b>AI:</b> {msg.text}
        </div>
      );
    }

    // -------------------------------
    // TEMPLES (can rename later → places)
    // -------------------------------
    if (msg.type === "temples") {
      return (
        <div key={i}>
          <b>🛕 Recommended Temples:</b>

          {msg.data.map((place, idx) => (
            <div
              key={idx}
              style={{
                border: "1px solid #ddd",
                borderRadius: "12px",
                padding: "10px",
                margin: "10px 0",
                background: "#fafafa"
              }}
            >
              <h4>{place.name}</h4>
              <p>⭐ {place.rating ?? "N/A"}</p>
              <p>👥 {place.crowd ?? "Unknown"}</p>

              {/* Open in Maps */}
              {place.lat && place.lng && (
                <button
                  onClick={() =>
                    window.open(
                      `https://www.google.com/maps?q=${place.lat},${place.lng}`,
                      "_blank"
                    )
                  }
                  style={{
                    marginTop: "8px",
                    padding: "6px 10px",
                    borderRadius: "6px",
                    border: "none",
                    background: "#28a745",
                    color: "white",
                    cursor: "pointer"
                  }}
                >
                  📍 Open in Maps
                </button>
              )}
            </div>
          ))}
        </div>
      );
    }

    // -------------------------------
    // MAP
    // -------------------------------
    if (msg.type === "map") {

      const originalUrl = msg.data;

      // Safe fallback search query
      let embedUrl =
        "https://www.google.com/maps?q=temples+in+nashik&output=embed";

      try {
        // Extract city or keyword from URL if possible
        const decoded = decodeURIComponent(originalUrl);

        if (decoded.toLowerCase().includes("nashik")) {
          embedUrl =
            "https://www.google.com/maps?q=temples+in+nashik&output=embed";
        }

      } catch (e) {
        console.log("Map URL parse failed, using fallback");
      }

      return (
        <div key={i} style={{ margin: "10px 0" }}>
          <b>🗺 Location Map:</b>

          <iframe
            src={embedUrl}
            width="100%"
            height="350"
            style={{
              border: 0,
              borderRadius: "10px",
              marginTop: "8px"
            }}
            loading="lazy"
            title="Google Map"
          />

          <div style={{ marginTop: "8px" }}>
            <button
              onClick={() => window.open(originalUrl, "_blank")}
              style={{
                padding: "6px 10px",
                borderRadius: "6px",
                border: "none",
                background: "#28a745",
                color: "white",
                cursor: "pointer"
              }}
            >
              📍 Open Full Directions
            </button>
          </div>

        </div>
      );
    }

    // -------------------------------
    // TIPS
    // -------------------------------
    if (msg.type === "tips") {
      return (
        <div
          key={i}
          style={{
            background: "#f0f8ff",
            padding: "10px",
            margin: "10px 0",
            borderRadius: "8px"
          }}
        >
          💡 {msg.text}
        </div>
      );
    }

    return null;
  };

  // -------------------------------
  // Send Message (SSE)
  // -------------------------------
  const sendMessage = () => {
    if (!input.trim() || loading || !sessionId) return;

    const userMessage = { role: "user", text: input };
    const currentInput = input;

    setInput("");
    setLoading(true);

    // Close previous SSE connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    setMessages((prev) => [
      ...prev,
      userMessage,
      { role: "bot", text: "Typing...", type: "message" }
    ]);

    const eventSource = new EventSource(
      `http://127.0.0.1:8000/chat-stream?query=${encodeURIComponent(
        currentInput
      )}&session_id=${sessionId}` // <-- dynamic
    );

    eventSourceRef.current = eventSource;

    let botText = "";

    // -------------------------------
    // TEXT STREAM
    // -------------------------------
    eventSource.addEventListener("message", (event) => {
      botText += event.data;

      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: "bot",
          text: botText,
          type: "message"
        };
        return updated;
      });
    });

    // -------------------------------
    // TEMPLES (replace streaming)
    // -------------------------------
    eventSource.addEventListener("temples", (event) => {
      const data = JSON.parse(event.data);

      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: "bot",
          type: "temples",
          data
        };
        return updated;
      });
    });

    // -------------------------------
    // MAP (append)
    // -------------------------------
    eventSource.addEventListener("map", (event) => {
      const mapUrl = event.data;

      setMessages((prev) => [
        ...prev,
        {
          role: "bot",
          type: "map",
          data: mapUrl
        }
      ]);
    });

    // -------------------------------
    // TIPS (append)
    // -------------------------------
    eventSource.addEventListener("tip", (event) => {
      setMessages((prev) => [
        ...prev,
        { role: "bot", type: "tips", text: event.data }
      ]);
    });

    // -------------------------------
    // END
    // -------------------------------
    eventSource.addEventListener("end", () => {
      eventSource.close();
      setLoading(false);
    });

    // -------------------------------
    // ERROR (single handler)
    // -------------------------------
    eventSource.onerror = () => {
      eventSource.close();
      setLoading(false);

      setMessages((prev) => [
        ...prev,
        { role: "bot", type: "message", text: "⚠️ Error occurred" }
      ]);
    };
  };

  // -------------------------------
  // UI
  // -------------------------------
  return (
    <div style={{ maxWidth: "700px", margin: "auto", padding: "20px" }}>
      <h2>🛕 AI Travel Assistant</h2>

      <div
        style={{
          border: "1px solid #ccc",
          height: "400px",
          overflowY: "auto",
          padding: "10px",
          marginBottom: "10px",
          borderRadius: "10px",
          background: "#fff"
        }}
      >
        {messages.map(renderMessage)}
        <div ref={chatEndRef} />
      </div>

      <input
        style={{
          width: "75%",
          padding: "10px",
          borderRadius: "8px",
          border: "1px solid #ccc"
        }}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && sendMessage()}
        placeholder="Ask about temples, travel plans..."
      />

      <button
        onClick={sendMessage}
        disabled={loading || !sessionId}
        style={{
          padding: "10px 15px",
          marginLeft: "10px",
          borderRadius: "8px",
          border: "none",
          background: loading ? "#999" : "#007bff",
          color: "white",
          cursor: loading ? "not-allowed" : "pointer"
        }}
      >
        {loading ? "..." : "Send"}
      </button>
      <DeleteMemoryButton
        sessionId={sessionId}
        onDeleted={async () => {
          try {
            setMessages([]);

            // remove old session
            localStorage.removeItem("session_id");

            const res = await fetch(
              "http://127.0.0.1:8000/api/get-session-id"
            );

            const data = await res.json();

            localStorage.setItem(
              "session_id",
              data.session_id
            );

            setSessionId(data.session_id);

          } catch (err) {
            console.error("Failed to create new session", err);
          }
        }}
      />
    </div>
  );
}

export default App;