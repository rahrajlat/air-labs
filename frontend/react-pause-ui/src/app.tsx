import React, { useState } from "react";
import { createRoot } from "react-dom/client";

// For local dev (served at http://127.0.0.1:5173), call Airflow directly:
// const API_BASE = "http://127.0.0.1:8080/api/airflow-tools-api";
const API_BASE = "/api/airflow-bulk-pause-api";
//const API_BASE = "http://127.0.0.1:8080/api/airflow-tools-api";
// When you copy into Airflow later, change the above to: const API_BASE = "/api/airflow-tools-api";

async function callApi(action: "pause" | "unpause", name_prefix: string, tagsCsv: string) {
  const qs = new URLSearchParams();
  if (name_prefix) qs.set("name_prefix", name_prefix);
  if (tagsCsv) qs.set("tags", tagsCsv);
  const base =
    action === "pause" ? `${API_BASE}/pause_dags/` : `${API_BASE}/unpause_dags/`;
  const res = await fetch(`${base}?${qs.toString()}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

function App() {
  const [action, setAction] = useState<"pause" | "unpause">("pause");
  const [namePrefix, setNamePrefix] = useState("dag_");
  const [tagsCsv, setTagsCsv] = useState("analytics, web");
  const [loading, setLoading] = useState(false);
  const [count, setCount] = useState<number | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [out, setOut] = useState<any>(null);

  const run = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true); setErr(null); setCount(null); setOut(null);
    try {
      const data = await callApi(action, namePrefix, tagsCsv);
      setOut(data);
      setCount(Array.isArray(data?.result) ? data.result.length : 0);
    } catch (e: any) {
      setErr(String(e.message || e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ background:"#111827", border:"1px solid #334155", borderRadius:12, padding:16, color:"#e5e7eb", fontFamily:"system-ui", maxWidth:560, margin:"40px auto" }}>
      <h2 style={{ marginTop:0 }}>Pause / Unpause DAGs</h2>

      <form onSubmit={run} style={{ display:"grid", gap:12 }}>
        <label>Action:&nbsp;
          <select value={action} onChange={e => setAction(e.target.value as any)}>
            <option value="pause">pause</option>
            <option value="unpause">unpause</option>
          </select>
        </label>
        <label>Name prefix:&nbsp;
          <input value={namePrefix} onChange={e => setNamePrefix(e.target.value)} />
        </label>
        <label>Tags (CSV):&nbsp;
          <input value={tagsCsv} onChange={e => setTagsCsv(e.target.value)} />
        </label>
        <button disabled={loading} style={{ background:"#2563eb", color:"#fff", border:"none", padding:"10px", borderRadius:8 }}>
          {loading ? "Working…" : "Run"}
        </button>
      </form>

      {err && <div style={{ color:"#f87171", marginTop:10 }}>❌ {err}</div>}
      {count !== null && !err && <div style={{ marginTop:10, color:"#86efac" }}>✅ DAGs affected: {count}</div>}

      {out && (
        <pre style={{ marginTop:12, background:"#0b1530", padding:10, borderRadius:8, border:"1px solid #334155", overflow:"auto" }}>
{JSON.stringify(out, null, 2)}
        </pre>
      )}
    </div>
  );
}

createRoot(document.getElementById("root")!).render(<App />);