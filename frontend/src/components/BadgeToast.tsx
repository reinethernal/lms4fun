import type { AwardedBadge } from '@/api/types';

interface BadgeToastProps {
  badge: AwardedBadge;
  onDismiss: () => void;
}

export function BadgeToast({ badge, onDismiss }: BadgeToastProps) {
  const icon = badge.icon_url?.startsWith('http') ? (
    <img src={badge.icon_url} alt="" className="badge-toast-icon-img" />
  ) : (
    <span className="badge-toast-icon-emoji">{badge.icon_url || '🏅'}</span>
  );

  return (
    <div className={`badge-toast badge-level-${badge.level || 'bronze'}`} role="status">
      <div className="badge-toast-icon">{icon}</div>
      <div className="badge-toast-body">
        <p className="badge-toast-title">Новый бейдж!</p>
        <p className="badge-toast-name">{badge.title}</p>
        {badge.description && (
          <p className="badge-toast-desc">{badge.description}</p>
        )}
      </div>
      <button type="button" className="badge-toast-close" onClick={onDismiss} aria-label="Закрыть">
        ×
      </button>
    </div>
  );
}
