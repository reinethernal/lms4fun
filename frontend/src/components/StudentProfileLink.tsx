import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';

interface Props {
  userId: number;
  children: ReactNode;
  className?: string;
}

export function StudentProfileLink({ userId, children, className }: Props) {
  return (
    <Link to={`/students/${userId}`} className={`profile-link${className ? ` ${className}` : ''}`}>
      {children}
    </Link>
  );
}
