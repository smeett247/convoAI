import { BrowserRouter as Router, Route, Routes, Navigate } from "react-router-dom";
import Chatbot from "./chatbot"; 
import Form from "./form"; 

function Home() {
  return (
    <section className="px-72 bg-slate-100 relative max-md:px-10">
      <h1 className="text-3xl font-bold text-center py-10">Welcome to the Alunet Home Page</h1>
    </section>
  );
}

function App() {
  return (
    <main>
      <Routes>
        <Route path="/home" element={<Home />} />
        <Route path="/chatbot" element={<Chatbot />} />
        <Route path="/form" element={<Form />} />
        <Route path="/" element={<Navigate to="/form" replace />} />
        <Route path="*" element={<Navigate to="/home" replace />} /> 
      </Routes>
    </main>
  );
}

export default function AppWrapper() {
  return (
    <Router>
      <App />
    </Router>
  );
}










