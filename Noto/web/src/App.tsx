import { Link, NavLink, Route, Routes } from "react-router-dom";
import { ConfigProvider } from "./store/config";
import ConfigPage from "./pages/ConfigPage";
import NotebooksPage from "./pages/NotebooksPage";
import NotebookDetail from "./pages/NotebookDetail";

export default function App() {
  return (
    <ConfigProvider>
      <nav>
        <Link to="/" style={{ fontWeight: "bold" }}>Noto</Link>
        <NavLink to="/">空间</NavLink>
        <NavLink to="/config">设置</NavLink>
      </nav>
      <div className="container">
        <Routes>
          <Route path="/" element={<NotebooksPage />} />
          <Route path="/notebooks/:id" element={<NotebookDetail />} />
          <Route path="/config" element={<ConfigPage />} />
        </Routes>
      </div>
    </ConfigProvider>
  );
}
