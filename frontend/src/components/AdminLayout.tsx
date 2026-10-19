import { NavLink, Outlet } from 'react-router-dom';
import { isSuperAdmin } from '@/api/client';
import { useAuth } from '@/context/AuthContext';

const links = [
  { to: '/admin', label: 'Обзор', end: true },
  { to: '/admin/users', label: 'Пользователи' },
  { to: '/admin/groups', label: 'Группы' },
  { to: '/admin/badges', label: 'Бейджи' },
  { to: '/admin/courses', label: 'Курсы' },
  { to: '/admin/submissions', label: 'Решения' },
  { to: '/admin/parents', label: 'Родители' },
];

export function AdminLayout() {
  const { user } = useAuth();
  const showDjangoAdmin = user && isSuperAdmin(user.role);

  return (
    <div className="admin-layout">
      <aside className="admin-sidebar admin-sidebar-desktop">
        <h3>Админ-панель</h3>
        <nav>
          {links.map((link) => (
            <NavLink key={link.to} to={link.to} end={link.end}>
              {link.label}
            </NavLink>
          ))}
          {showDjangoAdmin && (
            <a href="/django-admin/" target="_blank" rel="noopener noreferrer" className="admin-external-link">
              Django Admin
            </a>
          )}
        </nav>
      </aside>
      <nav className="admin-tabs" aria-label="Админ-навигация">
        {links.map((link) => (
          <NavLink key={link.to} to={link.to} end={link.end}>
            {link.label}
          </NavLink>
        ))}
        {showDjangoAdmin && (
          <a href="/django-admin/" target="_blank" rel="noopener noreferrer">
            Django Admin
          </a>
        )}
      </nav>
      <div>
        <Outlet />
      </div>
    </div>
  );
}
