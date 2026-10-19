import { FormEvent, useMemo, useState } from 'react';
import { api } from '@/api/client';
import type { User } from '@/api/types';

interface Props {
  user: User;
  onUpdated: () => void;
}

export function ProfileSettingsForm({ user, onUpdated }: Props) {
  const [displayName, setDisplayName] = useState(user.display_name);
  const [avatarUrl, setAvatarUrl] = useState('');
  const [avatarFile, setAvatarFile] = useState<File | null>(null);
  const [removeAvatar, setRemoveAvatar] = useState(false);
  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const previewUrl = useMemo(() => {
    if (avatarFile) {
      return URL.createObjectURL(avatarFile);
    }
    if (removeAvatar) {
      return '';
    }
    return user.avatar;
  }, [avatarFile, removeAvatar, user.avatar]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError('');
    setSuccess('');
    try {
      if (avatarFile || removeAvatar) {
        const formData = new FormData();
        formData.append('display_name', displayName);
        if (avatarFile) {
          formData.append('avatar_image', avatarFile);
        }
        if (removeAvatar) {
          formData.append('remove_avatar', 'true');
        }
        if (avatarUrl.trim()) {
          formData.append('avatar', avatarUrl.trim());
        }
        if (password) {
          formData.append('password', password);
          formData.append('password_confirm', passwordConfirm);
        }
        await api.profile.update(formData);
      } else {
        const payload: {
          display_name?: string;
          avatar?: string;
          password?: string;
          password_confirm?: string;
        } = {
          display_name: displayName,
        };
        if (avatarUrl.trim()) {
          payload.avatar = avatarUrl.trim();
        }
        if (password) {
          payload.password = password;
          payload.password_confirm = passwordConfirm;
        }
        await api.profile.update(payload);
      }
      setPassword('');
      setPasswordConfirm('');
      setAvatarFile(null);
      setAvatarUrl('');
      setRemoveAvatar(false);
      setSuccess('Профиль обновлён.');
      onUpdated();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сохранить');
    } finally {
      setBusy(false);
    }
  }

  function handleFileChange(file: File | null) {
    setAvatarFile(file);
    setRemoveAvatar(false);
    if (file) {
      setAvatarUrl('');
    }
  }

  return (
    <form className="card profile-settings-form" onSubmit={(e) => void handleSubmit(e)}>
      <h2>Настройки профиля</h2>
      {error && <div className="error-banner">{error}</div>}
      {success && <div className="success-banner">{success}</div>}

      <div className="form-group">
        <label>Отображаемое имя</label>
        <input value={displayName} onChange={(e) => setDisplayName(e.target.value)} />
      </div>

      <div className="form-group">
        <label>Аватар</label>
        {previewUrl ? (
          <div className="profile-settings-preview">
            <img src={previewUrl} alt="" className="profile-avatar-img" />
          </div>
        ) : (
          <p className="text-muted text-sm">Аватар не задан</p>
        )}
        <input
          type="file"
          accept="image/jpeg,image/png,image/webp,image/gif"
          onChange={(e) => handleFileChange(e.target.files?.[0] ?? null)}
        />
        <p className="hint-text">JPEG, PNG, WebP или GIF, до 2 МБ</p>
        {user.avatar && !avatarFile && (
          <label className="mt-sm">
            <input
              type="checkbox"
              checked={removeAvatar}
              onChange={(e) => setRemoveAvatar(e.target.checked)}
            />
            {' '}Удалить текущий аватар
          </label>
        )}
      </div>

      <div className="form-group">
        <label>Или URL картинки</label>
        <input
          type="url"
          value={avatarUrl}
          onChange={(e) => {
            setAvatarUrl(e.target.value);
            if (e.target.value) {
              setAvatarFile(null);
              setRemoveAvatar(false);
            }
          }}
          placeholder="https://..."
          disabled={Boolean(avatarFile)}
        />
        <p className="hint-text">Ссылка на изображение в интернете (если не загружаете файл)</p>
      </div>

      <div className="form-group">
        <label>Новый пароль</label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          minLength={6}
          autoComplete="new-password"
        />
      </div>

      <div className="form-group">
        <label>Подтверждение пароля</label>
        <input
          type="password"
          value={passwordConfirm}
          onChange={(e) => setPasswordConfirm(e.target.value)}
          minLength={6}
          autoComplete="new-password"
        />
      </div>

      <button type="submit" className="btn btn-primary" disabled={busy}>
        {busy ? 'Сохранение…' : 'Сохранить'}
      </button>
    </form>
  );
}
