import type { User } from '@/api/types';

interface Props {
  user: User;
  subtitle?: string;
}

function formatDate(value: string | null) {
  if (!value) return '—';
  return new Date(value).toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
}

export function ProfileHeader({ user, subtitle }: Props) {
  const initials = (user.display_name || user.username).slice(0, 1).toUpperCase();

  return (
    <div className="profile-header card">
      <div className="profile-avatar">
        {user.avatar ? (
          <img src={user.avatar} alt="" className="profile-avatar-img" />
        ) : (
          <span className="profile-avatar-fallback">{initials}</span>
        )}
      </div>
      <div className="profile-header-body">
        <h1 className="profile-name">{user.display_name || user.username}</h1>
        {subtitle && <p className="text-muted">{subtitle}</p>}
        <p className="text-sm text-muted mt-sm">
          Логин: {user.username}
          {' · '}
          На платформе с {formatDate(user.date_joined)}
          {user.last_login && (
            <>
              {' · '}
              Последний вход: {new Date(user.last_login).toLocaleString('ru-RU')}
            </>
          )}
        </p>
      </div>
    </div>
  );
}
