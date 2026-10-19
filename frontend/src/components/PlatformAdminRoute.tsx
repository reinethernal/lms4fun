import { Navigate } from 'react-router-dom';
import { isPlatformAdmin } from '@/api/client';
import { useAuth } from '@/context/AuthContext';
import { Loading } from './Loading';

export function PlatformAdminRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();

  if (loading) return <Loading />;
  if (!user) return <Navigate to="/login" replace />;
  if (!isPlatformAdmin(user.role)) return <Navigate to="/admin" replace />;

  return <>{children}</>;
}
