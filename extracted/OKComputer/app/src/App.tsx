import { Routes, Route } from "react-router"
import Home from "./pages/Home"
import AgentDetail from "./pages/AgentDetail"
import Logs from "./pages/Logs"
import Login from "./pages/Login"
import NotFound from "./pages/NotFound"

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/agent/:id" element={<AgentDetail />} />
      <Route path="/logs" element={<Logs />} />
      <Route path="/login" element={<Login />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}
