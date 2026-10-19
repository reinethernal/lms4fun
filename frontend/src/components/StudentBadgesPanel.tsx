import { FormEvent, useCallback, useEffect, useState } from 'react';
import { api } from '@/api/client';
import type { Badge, UserBadge } from '@/api/types';
import { Loading } from '@/components/Loading';

type Mode = 'readonly' | 'manage';

interface Props {
  userId: number;
  mode: Mode;
  fetchBadges?: (userId: number) => Promise<UserBadge[]>;
  initialBadges?: UserBadge[];
  onBadgesChange?: () => void;
}

function formatDate(value: string) {
  return new Date(value).toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
}

export function StudentBadgesPanel({
  userId,
  mode,
  fetchBadges,
  initialBadges,
  onBadgesChange,
}: Props) {
  const [badges, setBadges] = useState<UserBadge[]>(initialBadges ?? []);
  const [allBadges, setAllBadges] = useState<Badge[]>([]);
  const [selectedBadgeId, setSelectedBadgeId] = useState<number | ''>('');
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const loadBadges = useCallback(async () => {
    if (initialBadges && mode === 'readonly' && !fetchBadges) {
      setBadges(initialBadges);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError('');
    try {
      const data = fetchBadges
        ? await fetchBadges(userId)
        : await api.admin.users.badges.list(userId);
      setBadges(data);
    } catch {
      setError('Не удалось загрузить бейджи');
    } finally {
      setLoading(false);
    }
  }, [userId, fetchBadges, initialBadges, mode]);

  useEffect(() => {
    void loadBadges();
  }, [loadBadges]);

  useEffect(() => {
    if (initialBadges) {
      setBadges(initialBadges);
    }
  }, [initialBadges]);

  useEffect(() => {
    if (mode !== 'manage') return;
    void (async () => {
      try {
        const data = await api.admin.badges.list();
        setAllBadges(data.filter((b) => b.is_active));
      } catch {
        setError('Не удалось загрузить список бейджей');
      }
    })();
  }, [mode]);

  const earnedIds = new Set(badges.map((b) => b.badge.id));
  const availableBadges = allBadges.filter((b) => !earnedIds.has(b.id));

  async function handleAward(e: FormEvent) {
    e.preventDefault();
    if (!selectedBadgeId) return;
    setBusy(true);
    setError('');
    try {
      await api.admin.users.badges.award(userId, Number(selectedBadgeId));
      setSelectedBadgeId('');
      await loadBadges();
      onBadgesChange?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось выдать бейдж');
    } finally {
      setBusy(false);
    }
  }

  async function handleRevoke(badgeId: number, title: string) {
    if (!window.confirm(`Отозвать бейдж «${title}»?`)) return;
    setBusy(true);
    setError('');
    try {
      await api.admin.users.badges.revoke(userId, badgeId);
      await loadBadges();
      onBadgesChange?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось отозвать бейдж');
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <Loading />;

  return (
    <div className="student-badges-panel">
      {error && <div className="error-banner">{error}</div>}

      {mode === 'manage' && (
        <form className="flex-wrap-gap mb-md" onSubmit={(e) => void handleAward(e)}>
          <select
            value={selectedBadgeId}
            onChange={(e) => setSelectedBadgeId(e.target.value ? Number(e.target.value) : '')}
            disabled={busy || availableBadges.length === 0}
          >
            <option value="">Выберите бейдж…</option>
            {availableBadges.map((b) => (
              <option key={b.id} value={b.id}>
                {b.icon || '🏅'} {b.title}
              </option>
            ))}
          </select>
          <button
            type="submit"
            className="btn btn-primary btn-compact"
            disabled={busy || !selectedBadgeId}
          >
            Выдать бейдж
          </button>
        </form>
      )}

      {badges.length === 0 ? (
        <p className="text-muted">Пока нет бейджей</p>
      ) : (
        <div className="student-badges-grid">
          {badges.map((ub) => (
            <div key={ub.id} className="student-badge-card card">
              <div className="student-badge-icon">
                {ub.badge.icon_url || ub.badge.icon || '🏅'}
              </div>
              <div className="student-badge-body">
                <strong>{ub.badge.title}</strong>
                {ub.badge.level && <span className="badge ml-sm">{ub.badge.level}</span>}
                <p className="text-muted text-sm mt-sm">{ub.badge.description}</p>
                <p className="text-sm mt-sm">
                  Получен: {formatDate(ub.awarded_at)}
                  {ub.source === 'manual' && ub.awarded_by && (
                    <span className="text-muted"> · вручную</span>
                  )}
                </p>
              </div>
              {mode === 'manage' && ub.source === 'manual' && (
                <button
                  type="button"
                  className="btn btn-danger btn-compact"
                  disabled={busy}
                  onClick={() => void handleRevoke(ub.badge.id, ub.badge.title)}
                >
                  Отозвать
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
