import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Memory from './pages/Memory';
import Tasks from './pages/Tasks';
import Skills from './pages/Skills';
import Logs from './pages/Logs';
import Settings from './pages/Settings';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="memory" element={<Memory />} />
          <Route path="tasks" element={<Tasks />} />
          <Route path="skills" element={<Skills />} />
          <Route path="logs" element={<Logs />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
