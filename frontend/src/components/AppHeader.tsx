import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { isParentRole, isStaffRole } from '@/api/client';
import { useAuth } from '@/context/AuthContext';

export function AppHeader() {
  const { user, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);

  function closeMenu() {
    setMenuOpen(false);
  }

  const navLinks = (
    <>
      <NavLink to="/" end onClick={closeMenu}>
        {user && isParentRole(user.role) ? 'Кабинет родителя' : 'Кабинет'}
      </NavLink>
      {user && isParentRole(user.role) && (
        <NavLink to="/children" onClick={closeMenu}>
          Мои дети
        </NavLink>
      )}
      <NavLink to="/leaderboard" onClick={closeMenu}>
        Рейтинг
      </NavLink>
      <NavLink to="/profile" onClick={closeMenu}>
        Профиль
      </NavLink>
      {user && isStaffRole(user.role) && (
        <NavLink to="/admin" onClick={closeMenu}>
          Админка
        </NavLink>
      )}
    </>
  );

  return (
    <>
      <header className="app-header">
        <NavLink to="/" className="app-brand" onClick={closeMenu}>
          CodeLearn
        </NavLink>
        <nav className="app-nav app-nav-desktop">
          {navLinks}
          {user && (
            <NavLink to="/profile" className="user-info" onClick={closeMenu}>
              {user.display_name || user.username}
            </NavLink>
          )}
          <button type="button" className="btn btn-secondary" onClick={() => void logout()}>
            Выйти
          </button>
        </nav>
        <button
          type="button"
          className="app-header-toggle"
          aria-label="Меню"
          aria-expanded={menuOpen}
          onClick={() => setMenuOpen((v) => !v)}
        >
          ☰
        </button>
      </header>

      <div
        className={`app-nav-overlay${menuOpen ? ' nav-open' : ''}`}
        onClick={closeMenu}
        aria-hidden={!menuOpen}
      />

      <nav
        className={`app-nav-mobile-panel${menuOpen ? ' nav-open' : ''}`}
        aria-hidden={!menuOpen}
      >
        {user && (
          <NavLink to="/profile" className="app-nav-mobile-user" onClick={closeMenu}>
            {user.display_name || user.username}
          </NavLink>
        )}
        {navLinks}
        <button
          type="button"
          className="btn btn-secondary mt-auto"
          onClick={() => {
            closeMenu();
            void logout();
          }}
        >
          Выйти
        </button>
      </nav>
    </>
  );
}
