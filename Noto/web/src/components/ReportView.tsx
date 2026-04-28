import { useEffect, useState } from "react";
import { Report, reportApi } from "../api/client";

function today() { return new Date().toISOString().slice(0, 10); }
function daysAgo(n: number) {
  const d = new Date(); d.setDate(d.getDate() - n);
  return d.toISOString().slice(0, 10);
}

export default function ReportView({ notebookId }: { notebookId: string }) {
  const [reports, setReports] = useState<Report[]>([]);
  const [busy, setBusy] = useState(false);
  const [from, setFrom] = useState(daysAgo(7));
  const [to, setTo] = useState(today());

  const reload = async () => setReports(await reportApi.list(notebookId));
  useEffect(() => { reload(); }, [notebookId]);

  const onGenerate = async () => {
    setBusy(true);
    try {
      await reportApi.generate({ notebook_id: notebookId, from_date: from, to_date: to });
      await reload();
    } finally {
      setBusy(false);
    }
  };

  return (
    <div>
      <div className="card">
        <h3>生成新报告</h3>
        <label>起：</label><input type="date" value={from} onChange={(e) => setFrom(e.target.value)} />
        <label>止：</label><input type="date" value={to} onChange={(e) => setTo(e.target.value)} />
        <button className="primary" onClick={onGenerate} disabled={busy} style={{ marginTop: 8 }}>
          {busy ? "生成中..." : "生成报告"}
        </button>
      </div>

      {reports.map((r) => (
        <div key={r.id} className="card">
          <h3>{r.from_date} → {r.to_date}</h3>
          <pre style={{ whiteSpace: "pre-wrap", fontFamily: "inherit" }}>{r.content}</pre>
          <small style={{ color: "#888" }}>生成于 {r.generated_at}</small>
        </div>
      ))}
    </div>
  );
}
