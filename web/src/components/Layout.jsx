import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import TopBar from './TopBar';
import StatusBar from './StatusBar';

export default function Layout() {
  return (
    <>
      <div className="grid-bg" />
      <div className="app-layout">
        <Sidebar />
        <div className="main-content">
          <TopBar />
          <div className="page-content">
            <Outlet />
          </div>
          <StatusBar />
        </div>
      </div>
    </>
  );
}
