import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api, isPlatformAdmin, isSuperAdmin } from '@/api/client';
import type { TelegramBotSettings, TelegramLinkCode, TelegramStatus } from '@/api/types';
import { useAuth } from '@/context/AuthContext';

export function AdminIndexPage() {
  const { user } = useAuth();
  const canManageBot = Boolean(user && isPlatformAdmin(user.role));

  const [tg, setTg] = useState<TelegramStatus | null>(null);
  const [botSettings, setBotSettings] = useState<TelegramBotSettings | null>(null);
  const [linkCode, setLinkCode] = useState<TelegramLinkCode | null>(null);
  const [tgError, setTgError] = useState('');
  const [tgBusy, setTgBusy] = useState(false);
  const [formEnabled, setFormEnabled] = useState(false);
  const [formToken, setFormToken] = useState('');
  const [formUsername, setFormUsername] = useState('');
  const [formProxy, setFormProxy] = useState('');
  const [formNotifyAll, setFormNotifyAll] = useState(false);
  const [savedHint, setSavedHint] = useState('');

  const loadTelegram = useCallback(async () => {
    try {
      const status = await api.admin.telegram.status();
      setTg(status);
      setTgError('');
      if (canManageBot) {
        const settings = await api.admin.telegram.getBotSettings();
        setBotSettings(settings);
        setFormEnabled(settings.enabled);
        setFormUsername(settings.bot_username);
        setFormProxy(settings.http_proxy);
        setFormNotifyAll(settings.notify_all_submissions);
        setFormToken('');
      }
    } catch {
      setTgError('Не удалось загрузить статус Telegram');
    }
  }, [canManageBot]);

  useEffect(() => {
    void loadTelegram();
  }, [loadTelegram]);

  async function saveBotSettings() {
    setTgBusy(true);
    setTgError('');
    setSavedHint('');
    try {
      const payload: Parameters<typeof api.admin.telegram.updateBotSettings>[0] = {
        enabled: formEnabled,
        bot_username: formUsername,
        http_proxy: formProxy,
        notify_all_submissions: formNotifyAll,
      };
      if (formToken.trim()) {
        payload.bot_token = formToken.trim();
      }
      const settings = await api.admin.telegram.updateBotSettings(payload);
      setBotSettings(settings);
      setFormToken('');
      setSavedHint(
        settings.is_ready
          ? 'Сохранено. Если меняли токен или proxy — перезапустите сервисы (start-all.sh), чтобы бот подхватил настройки.'
          : 'Сохранено. Включите бота и укажите токен, чтобы начать работу.',
      );
      await loadTelegram();
    } catch {
      setTgError('Не удалось сохранить настройки бота');
    } finally {
      setTgBusy(false);
    }
  }

  async function clearToken() {
    if (!window.confirm('Удалить сохранённый токен бота?')) return;
    setTgBusy(true);
    try {
      const settings = await api.admin.telegram.updateBotSettings({ clear_bot_token: true });
      setBotSettings(settings);
      setFormToken('');
      await loadTelegram();
    } catch {
      setTgError('Не удалось очистить токен');
    } finally {
      setTgBusy(false);
    }
  }

  async function createLinkCode() {
    setTgBusy(true);
    setTgError('');
    try {
      setLinkCode(await api.admin.telegram.createLinkCode());
    } catch {
      setTgError('Не удалось создать код привязки');
    } finally {
      setTgBusy(false);
    }
  }

  async function unlinkTelegram() {
    setTgBusy(true);
    try {
      await api.admin.telegram.unlink();
      setLinkCode(null);
      await loadTelegram();
    } catch {
      setTgError('Не удалось отвязать Telegram');
    } finally {
      setTgBusy(false);
    }
  }

  async function toggleNotify(field: 'notify_manual_review' | 'notify_new_submissions') {
    if (!tg?.linked) return;
    setTgBusy(true);
    try {
      setTg(await api.admin.telegram.updateSettings({ [field]: !tg[field] }));
    } catch {
      setTgError('Не удалось сохранить настройки');
    } finally {
      setTgBusy(false);
    }
  }

  return (
    <div>
      <h1 className="page-title">Админ-панель</h1>
      <p className="text-muted mb-lg">
        Управление пользователями, группами, курсами и решениями.
      </p>
      <div className="card-grid">
        <Link to="/admin/users" className="card card-link">
          <h3>Пользователи</h3>
          <p className="text-muted">Создание и редактирование учётных записей</p>
        </Link>
        <Link to="/admin/groups" className="card card-link">
          <h3>Группы</h3>
          <p className="text-muted">Учебные группы и состав</p>
        </Link>
        <Link to="/admin/badges" className="card card-link">
          <h3>Бейджи</h3>
          <p className="text-muted">Создание бейджей с кастомными иконками</p>
        </Link>
        <Link to="/admin/courses" className="card card-link">
          <h3>Курсы и уроки</h3>
          <p className="text-muted">Курсы, уроки, задания и импорт контента</p>
        </Link>
        <Link to="/admin/submissions" className="card card-link">
          <h3>Решения</h3>
          <p className="text-muted">Просмотр отправленных решений</p>
        </Link>
        <Link to="/admin/parents" className="card card-link">
          <h3>Родители и дети</h3>
          <p className="text-muted">Привязка учеников к родителям</p>
        </Link>
        {user && isSuperAdmin(user.role) && (
          <a
            href="/django-admin/"
            target="_blank"
            rel="noopener noreferrer"
            className="card card-link"
          >
            <h3>Django Admin</h3>
            <p className="text-muted">Низкоуровневая панель Django (модели, миграции)</p>
          </a>
        )}
      </div>

      <section className="card mt-lg">
        <h2>Telegram-бот для проверки решений</h2>
        <p className="text-muted">
          Получайте уведомления о новых решениях и принимайте / отклоняйте / комментируйте
          прямо в Telegram.
        </p>
        {tgError && <p className="error-text">{tgError}</p>}
        {savedHint && <p className="hint-text">{savedHint}</p>}

        {canManageBot && (
          <div className="stack gap-sm mb-lg">
            <h3>Настройки бота</h3>
            {!botSettings ? (
              <p className="text-muted">Загрузка настроек…</p>
            ) : (
              <>
                <label className="checkbox-row">
                  <input
                    type="checkbox"
                    checked={formEnabled}
                    disabled={tgBusy}
                    onChange={(e) => setFormEnabled(e.target.checked)}
                  />
                  Бот включён
                </label>
                <div className="form-group">
                  <label>
                    Токен бота
                    <input
                      type="password"
                      autoComplete="off"
                      placeholder={
                        botSettings.bot_token_set
                          ? `Сохранён: ${botSettings.bot_token_masked}`
                          : 'Вставьте токен от @BotFather'
                      }
                      value={formToken}
                      disabled={tgBusy}
                      onChange={(e) => setFormToken(e.target.value)}
                    />
                  </label>
                </div>
                {botSettings.bot_token_set && (
                  <button type="button" className="btn btn-secondary btn-sm" disabled={tgBusy} onClick={() => void clearToken()}>
                    Очистить токен
                  </button>
                )}
                <div className="form-group">
                  <label>
                    Username бота (без @)
                    <input
                      type="text"
                      value={formUsername}
                      disabled={tgBusy}
                      onChange={(e) => setFormUsername(e.target.value)}
                      placeholder="my_codelearn_bot"
                    />
                  </label>
                </div>
                <div className="form-group">
                  <label>
                    HTTP(S) proxy
                    <input
                      type="text"
                      value={formProxy}
                      disabled={tgBusy}
                      onChange={(e) => setFormProxy(e.target.value)}
                      placeholder="http://user:pass@host:8080"
                    />
                  </label>
                </div>
                <label className="checkbox-row">
                  <input
                    type="checkbox"
                    checked={formNotifyAll}
                    disabled={tgBusy}
                    onChange={(e) => setFormNotifyAll(e.target.checked)}
                  />
                  Уведомлять обо всех решениях (не только на ручной проверке)
                </label>
                <button type="button" className="btn btn-primary btn-sm" disabled={tgBusy} onClick={() => void saveBotSettings()}>
                  Сохранить настройки бота
                </button>
              </>
            )}
          </div>
        )}

        {!tg ? (
          <p className="text-muted">Загрузка…</p>
        ) : !tg.enabled ? (
          <p className="text-muted">
            {canManageBot
              ? 'Бот выключен или токен не задан. Заполните настройки выше и сохраните.'
              : 'Бот пока не настроен администратором платформы.'}
          </p>
        ) : tg.linked ? (
          <div className="stack gap-sm">
            <p>
              Привязан{tg.telegram_username ? <> (@{tg.telegram_username})</> : null}
              {tg.bot_username ? <> · бот @{tg.bot_username}</> : null}
            </p>
            <label className="checkbox-row">
              <input
                type="checkbox"
                checked={tg.notify_manual_review}
                disabled={tgBusy}
                onChange={() => void toggleNotify('notify_manual_review')}
              />
              Уведомления о решениях на ручной проверке
            </label>
            <label className="checkbox-row">
              <input
                type="checkbox"
                checked={tg.notify_new_submissions}
                disabled={tgBusy || !tg.notify_all_submissions}
                onChange={() => void toggleNotify('notify_new_submissions')}
              />
              Уведомления о всех решениях
              {!tg.notify_all_submissions ? ' (сначала включите в настройках бота)' : ''}
            </label>
            <button type="button" className="btn btn-secondary btn-sm" disabled={tgBusy} onClick={() => void unlinkTelegram()}>
              Отвязать Telegram
            </button>
          </div>
        ) : (
          <div className="stack gap-sm">
            <p className="text-muted">
              Создайте код и отправьте боту команду <code>/start КОД</code>
              {tg.bot_username ? <> (@{tg.bot_username})</> : null}.
            </p>
            <button type="button" className="btn btn-primary btn-sm" disabled={tgBusy} onClick={() => void createLinkCode()}>
              Создать код привязки
            </button>
            {linkCode && (
              <p>
                Код: <strong>{linkCode.code}</strong>
                <br />
                Команда: <code>{linkCode.start_command}</code>
              </p>
            )}
          </div>
        )}
      </section>
    </div>
  );
}
