import { Link, NavLink, Route, Routes } from "react-router-dom";
import { ConfigProvider } from "./store/config";
import ConfigPage from "./pages/ConfigPage";

export default function App() {
  return (
    <ConfigProvider>
      <nav>
        <Link to="/" style={{ fontWeight: "bold" }}>Noto</Link>
        <NavLink to="/config">设置</NavLink>
      </nav>
      <div className="container">
        <Routes>
          <Route path="/config" element={<ConfigPage />} />
        </Routes>
      </div>
    </ConfigProvider>
  );
}
