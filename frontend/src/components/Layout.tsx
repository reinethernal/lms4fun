import { Outlet } from 'react-router-dom';
import { AppHeader } from '@/components/AppHeader';

export function Layout() {
  return (
    <div className="app-shell">
      <AppHeader />
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  );
}
