"use client";

import { parseRate, shouldFail } from "@/lib/failure";
import { useEffect, useState } from "react";

type RequestRow = {
  id: number;
  requestId: string;
  text: string;
  status: string;
  result: string | null;
  createdAt: string;
};

export default function Home() {
  const [text, setText] = useState("");
  const [rows, setRows] = useState<RequestRow[]>([]);

  async function refresh() {
    const response = await fetch("/api/requests");
    setRows(await response.json());
  }

  async function submit() {
    if (!text.trim()) return;
    if (shouldFail(parseRate(process.env.NEXT_PUBLIC_WEB_CLIENT_FAILURE_RATE, 0.1))) {
      console.error("injected client failure");
      setText("");
      return;
    }
    await fetch("/api/submit", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ text }),
    });
    setText("");
    await refresh();
  }

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <main style={{ maxWidth: 720 }}>
      <h1>OpenTelemetry Experiment</h1>
      <p>Demo Pipeline: web → worker-api → redis → worker-worker → service (+ external api) → callback</p>

      <div style={{ display: "flex", gap: "0.5rem", margin: "1rem 0" }}>
        <input
          value={text}
          onChange={(event) => setText(event.target.value)}
          onKeyDown={(event) => event.key === "Enter" && submit()}
          placeholder="Enter some text"
          style={{ flex: 1, padding: "0.5rem" }}
        />
        <button onClick={submit} style={{ padding: "0.5rem 1rem" }}>
          Submit
        </button>
      </div>

      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            <th style={cell}>Request ID</th>
            <th style={cell}>Text</th>
            <th style={cell}>Status</th>
            <th style={cell}>Result</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.requestId}>
              <td style={cell}>{row.requestId.slice(0, 8)}</td>
              <td style={cell}>{row.text}</td>
              <td style={cell}>{row.status}</td>
              <td style={cell}>{row.result ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}

const cell: React.CSSProperties = {
  border: "1px solid #ddd",
  padding: "0.5rem",
  textAlign: "left",
};
