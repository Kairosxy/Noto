import { useState } from "react";
import { uploadDocument } from "../api/client";

export default function UploadZone({ notebookId, onUploaded }: { notebookId: string; onUploaded: () => void }) {
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

  const handle = async (f: File) => {
    setBusy(true); setMsg(`上传 ${f.name}...`);
    try {
      await uploadDocument(notebookId, f);
      setMsg(`已加入解析队列：${f.name}`);
      onUploaded();
    } catch (e) {
      setMsg(String(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div
      className="card"
      onDragOver={(e) => e.preventDefault()}
      onDrop={(e) => {
        e.preventDefault();
        const f = e.dataTransfer.files[0];
        if (f) handle(f);
      }}
      style={{ border: "2px dashed #ccc", textAlign: "center" }}
    >
      <p>拖拽文件到此处，或</p>
      <input
        type="file"
        disabled={busy}
        accept=".pdf,.txt,.md,.docx"
        onChange={(e) => e.target.files && e.target.files[0] && handle(e.target.files[0])}
      />
      <p style={{ color: "#666", fontSize: 12 }}>{msg}</p>
    </div>
  );
}
