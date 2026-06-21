import { Routes, Route } from "react-router";
import Layout from "./components/Layout";
import Home from "./pages/Home";
import Methodology from "./pages/Methodology";
import Markets from "./pages/Markets";
import Admin from "./pages/Admin";
import EmbedDemo from "./pages/EmbedDemo";
import Backtest from "./pages/Backtest";

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/methodology" element={<Methodology />} />
        <Route path="/markets" element={<Markets />} />
        <Route path="/admin" element={<Admin />} />
        <Route path="/embed-demo" element={<EmbedDemo />} />
        <Route path="/backtest" element={<Backtest />} />
      </Routes>
    </Layout>
  );
}

export default App;
