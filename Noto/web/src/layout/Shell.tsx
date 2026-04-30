import { ReactNode } from "react";

export default function Shell({
  sidebar, topbar, main, rightbar,
}: {
  sidebar: ReactNode;
  topbar?: ReactNode;
  main: ReactNode;
  rightbar?: ReactNode;
}) {
  return (
    <div style={{
      display: "grid",
      gridTemplateColumns: rightbar ? "220px 1fr 300px" : "220px 1fr",
      minHeight: "100vh",
    }}>
      <aside style={{
        background: "var(--bg-sidebar)",
        borderRight: "1px solid var(--border)",
        padding: "18px 14px",
        display: "flex",
        flexDirection: "column",
      }}>
        {sidebar}
      </aside>
      <main style={{ display: "flex", flexDirection: "column", minWidth: 0 }}>
        {topbar}
        <div style={{
          flex: 1,
          padding: "28px 36px 60px",
          maxWidth: 1000,
          width: "100%",
          margin: "0 auto",
          overflowY: "auto",
        }}>
          {main}
        </div>
      </main>
      {rightbar && (
        <aside style={{
          background: "var(--bg-drawer)",
          borderLeft: "1px solid var(--border)",
          padding: "18px 16px",
          overflowY: "auto",
          maxHeight: "100vh",
          position: "sticky",
          top: 0,
        }}>
          {rightbar}
        </aside>
      )}
    </div>
  );
}
