import { Navigate } from 'react-router-dom';
import { isStaffRole } from '@/api/client';
import { useAuth } from '@/context/AuthContext';
import { Loading } from './Loading';

export function StaffRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();

  if (loading) return <Loading />;
  if (!user) return <Navigate to="/login" replace />;
  if (!isStaffRole(user.role)) return <Navigate to="/" replace />;

  return <>{children}</>;
}
