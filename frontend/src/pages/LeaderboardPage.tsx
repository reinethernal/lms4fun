import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '@/api/client';
import { Loading } from '@/components/Loading';

export function LeaderboardPage() {
  const [entries, setEntries] = useState<Awaited<ReturnType<typeof api.leaderboard.list>>>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    void (async () => {
      try {
        setEntries(await api.leaderboard.list());
      } catch {
        setError('Не удалось загрузить рейтинг');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) return <Loading />;

  return (
    <div>
      <h1 className="page-title">Рейтинг</h1>
      {error && <div className="error-banner">{error}</div>}

      <div className="card">
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Место</th>
                <th>Ученик</th>
                <th>XP</th>
                <th>Заданий</th>
              </tr>
            </thead>
            <tbody>
              {entries.length === 0 ? (
                <tr>
                  <td colSpan={4} className="text-center-muted">
                    Рейтинг пока пуст
                  </td>
                </tr>
              ) : (
                entries.map((entry) => (
                  <tr key={entry.user_id}>
                    <td>#{entry.rank}</td>
                    <td>
                      <Link to={`/students/${entry.user_id}`}>
                        {entry.display_name || entry.username}
                      </Link>
                    </td>
                    <td>{entry.total_xp}</td>
                    <td>{entry.tasks_completed}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
