import { Navigate, Route, Routes } from "react-router-dom";
import Login from "./pages/Login";
import Cadastro from "./pages/Cadastro";
import Perfil from "./pages/Perfil";
import Verificacao from "./pages/Verificacao";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="/login" element={<Login />} />
      <Route path="/cadastro" element={<Cadastro />} />
      <Route path="/verificacao" element={<Verificacao />} />
      <Route path="/perfil" element={<Perfil />} />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}
