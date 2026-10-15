import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { HabitDetailPage } from "./pages/HabitDetailPage";
import { HabitsPage } from "./pages/HabitsPage";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/habits" element={<HabitsPage />} />
        <Route path="/habits/:habitId" element={<HabitDetailPage />} />
        <Route path="*" element={<Navigate to="/habits" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
