import { NavLink, Route, Routes } from "react-router";
import ReadyBanner from "./components/ReadyBanner";
import ChatPage from "./pages/ChatPage";
import DocumentsPage from "./pages/DocumentsPage";
import EvalPage from "./pages/EvalPage";

const navClass = ({ isActive }: { isActive: boolean }) =>
  "rounded-md px-3 py-2 text-sm font-medium " +
  (isActive ? "bg-slate-900 text-white" : "text-slate-700 hover:bg-slate-200");

export default function App() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="flex items-center gap-4 border-b border-slate-200 bg-white px-6 py-3">
        <span className="text-lg font-semibold">askPMO</span>
        <nav className="flex gap-1">
          <NavLink to="/" end className={navClass}>
            Chat
          </NavLink>
          <NavLink to="/documents" className={navClass}>
            Documents
          </NavLink>
          <NavLink to="/eval" className={navClass}>
            Evaluation
          </NavLink>
        </nav>
      </header>
      <ReadyBanner />
      <main className="p-6">
        <Routes>
          <Route path="/" element={<ChatPage />} />
          <Route path="/documents" element={<DocumentsPage />} />
          <Route path="/eval" element={<EvalPage />} />
        </Routes>
      </main>
    </div>
  );
}
