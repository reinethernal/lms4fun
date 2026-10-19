import { Navigate, Outlet } from 'react-router-dom';
import type { ReactNode } from 'react';
import { isParentRole } from '@/api/client';
import { useAuth } from '@/context/AuthContext';
import { Loading } from '@/components/Loading';

export function ParentRoute({ children }: { children?: ReactNode }) {
  const { user, loading } = useAuth();

  if (loading) return <Loading />;
  if (!user) return <Navigate to="/login" replace />;
  if (!isParentRole(user.role)) return <Navigate to="/" replace />;

  return children ?? <Outlet />;
}
