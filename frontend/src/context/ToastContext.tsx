import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import type { AwardedBadge } from '@/api/types';
import { BadgeToast } from '@/components/BadgeToast';

interface ToastItem {
  id: number;
  badge: AwardedBadge;
}

interface ToastContextValue {
  showBadgeToast: (badge: AwardedBadge) => void;
  showBadgeToasts: (badges: AwardedBadge[]) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const dismiss = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const showBadgeToast = useCallback((badge: AwardedBadge) => {
    const id = Date.now() + Math.random();
    setToasts((prev) => [...prev, { id, badge }]);
    window.setTimeout(() => dismiss(id), 5000);
  }, [dismiss]);

  const showBadgeToasts = useCallback((badges: AwardedBadge[]) => {
    badges.forEach((badge, index) => {
      window.setTimeout(() => showBadgeToast(badge), index * 400);
    });
  }, [showBadgeToast]);

  const value = useMemo(
    () => ({ showBadgeToast, showBadgeToasts }),
    [showBadgeToast, showBadgeToasts],
  );

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="toast-container" aria-live="polite">
        {toasts.map((toast) => (
          <BadgeToast
            key={toast.id}
            badge={toast.badge}
            onDismiss={() => dismiss(toast.id)}
          />
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    throw new Error('useToast must be used within ToastProvider');
  }
  return ctx;
}
