import { FormEvent, useEffect, useState } from "react";
import { api, streamSSE } from "../api/client";
import { useConfig } from "../store/config";

const PROVIDERS = ["openai", "anthropic", "google"];

export default function ConfigPage() {
  const { settings, reload } = useConfig();

  const [form, setForm] = useState({
    ai_provider: "openai",
    ai_api_key: "",
    ai_base_url: "",
    ai_model: "",
    embedding_provider: "",
    embedding_api_key: "",
    embedding_base_url: "",
    embedding_model: "",
    supabase_url: "",
    supabase_service_key: "",
  });
  const [testMsg, setTestMsg] = useState("");
  const [chatInput, setChatInput] = useState("");
  const [chatOut, setChatOut] = useState("");

  useEffect(() => {
    if (!settings) return;
    setForm((f) => ({
      ...f,
      ai_provider: settings.ai_provider || "openai",
      ai_base_url: settings.ai_base_url,
      ai_model: settings.ai_model,
      embedding_provider: settings.embedding_provider,
      embedding_base_url: settings.embedding_base_url,
      embedding_model: settings.embedding_model,
      supabase_url: settings.supabase_url,
    }));
  }, [settings]);

  const setField = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm({ ...form, [k]: e.target.value });

  const onSave = async (e: FormEvent) => {
    e.preventDefault();
    const body: Record<string, string> = {};
    for (const [k, v] of Object.entries(form)) if (v) body[k] = v;
    await api.updateSettings(body);
    await reload();
    setTestMsg("已保存");
  };

  const onTest = async () => {
    setTestMsg("测试中...");
    try {
      const key = form.ai_api_key || "__use_saved__";
      const r = await api.testConnection({
        provider: form.ai_provider,
        api_key: key,
        base_url: form.ai_base_url,
        model: form.ai_model,
      });
      setTestMsg(r.message);
    } catch (e: unknown) {
      setTestMsg(String(e));
    }
  };

  const onChat = async (e: FormEvent) => {
    e.preventDefault();
    setChatOut("");
    await streamSSE(
      "/api/ai/chat",
      { messages: [{ role: "user", content: chatInput }], system: "" },
      (d) => {
        if (d.content) setChatOut((s) => s + d.content);
        if (d.error) setChatOut((s) => s + `\n[ERROR] ${d.error}`);
      },
    );
  };

  return (
    <div>
      <div className="card">
        <h2>LLM 配置</h2>
        <form onSubmit={onSave}>
          <label>Provider</label>
          <select value={form.ai_provider} onChange={setField("ai_provider")}>
            {PROVIDERS.map((p) => <option key={p} value={p}>{p}</option>)}
          </select>

          <label>API Key {settings?.ai_api_key_set && "(已保存，留空即复用)"}</label>
          <input value={form.ai_api_key} onChange={setField("ai_api_key")} type="password" />

          <label>Base URL（可选）</label>
          <input value={form.ai_base_url} onChange={setField("ai_base_url")} placeholder="例：https://dashscope.aliyuncs.com/compatible-mode/v1" />

          <label>Chat Model</label>
          <input value={form.ai_model} onChange={setField("ai_model")} placeholder="gpt-4o / claude-sonnet-4-5 / qwen-plus" />

          <h3 style={{ marginTop: 24 }}>Embedding（留空则沿用 LLM 配置，但 model 必填）</h3>
          <label>Embedding Provider</label>
          <select value={form.embedding_provider} onChange={setField("embedding_provider")}>
            <option value="">(同 LLM)</option>
            {PROVIDERS.map((p) => <option key={p} value={p}>{p}</option>)}
          </select>
          <label>Embedding Base URL</label>
          <input value={form.embedding_base_url} onChange={setField("embedding_base_url")} />
          <label>Embedding Model</label>
          <input value={form.embedding_model} onChange={setField("embedding_model")} placeholder="text-embedding-3-small / text-embedding-v3" />

          <h3 style={{ marginTop: 24 }}>Supabase</h3>
          <label>Supabase URL</label>
          <input value={form.supabase_url} onChange={setField("supabase_url")} placeholder="https://xxx.supabase.co" />
          <label>Service Role Key {settings?.supabase_service_key_set && "(已保存)"}</label>
          <input value={form.supabase_service_key} onChange={setField("supabase_service_key")} type="password" />

          <div style={{ marginTop: 16, display: "flex", gap: 8 }}>
            <button className="primary" type="submit">保存</button>
            <button type="button" onClick={onTest}>测试 LLM 连接</button>
            <span style={{ alignSelf: "center", color: "#555" }}>{testMsg}</span>
          </div>
        </form>
      </div>

      <div className="card">
        <h2>随手测试聊天</h2>
        <form onSubmit={onChat}>
          <input value={chatInput} onChange={(e) => setChatInput(e.target.value)} placeholder="说点什么..." />
          <button className="primary" type="submit" style={{ marginTop: 8 }}>发送</button>
        </form>
        <pre style={{ marginTop: 12, whiteSpace: "pre-wrap" }}>{chatOut}</pre>
      </div>
    </div>
  );
}
