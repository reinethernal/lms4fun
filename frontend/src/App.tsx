import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AdminLayout } from '@/components/AdminLayout';
import { Layout } from '@/components/Layout';
import { ParentRoute } from '@/components/ParentRoute';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { PlatformAdminRoute } from '@/components/PlatformAdminRoute';
import { StaffRoute } from '@/components/StaffRoute';
import { AuthProvider } from '@/context/AuthContext';
import { ToastProvider } from '@/context/ToastContext';
import { CoursePage } from '@/pages/CoursePage';
import { DashboardPage } from '@/pages/DashboardPage';
import { LeaderboardPage } from '@/pages/LeaderboardPage';
import { LessonPage } from '@/pages/LessonPage';
import { LoginPage } from '@/pages/LoginPage';
import { ParentChildrenPage } from '@/pages/ParentChildrenPage';
import { AdminBadgesPage } from '@/pages/admin/AdminBadgesPage';
import { AdminCoursesPage } from '@/pages/admin/AdminCoursesPage';
import { AdminGroupsPage } from '@/pages/admin/AdminGroupsPage';
import { AdminIndexPage } from '@/pages/admin/AdminIndexPage';
import { AdminTaskEditPage } from '@/pages/admin/AdminTaskEditPage';
import { AdminLessonEditPage } from '@/pages/admin/AdminLessonEditPage';
import { AdminLessonsPage } from '@/pages/admin/AdminLessonsPage';
import { AdminParentsPage } from '@/pages/admin/AdminParentsPage';
import { AdminSubmissionsPage } from '@/pages/admin/AdminSubmissionsPage';
import { AdminUsersPage } from '@/pages/admin/AdminUsersPage';
import { StudentProfilePage } from '@/pages/StudentProfilePage';

export function App() {
  return (
    <AuthProvider>
      <ToastProvider>
        <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route index element={<DashboardPage />} />
            <Route path="courses/:id" element={<CoursePage />} />
            <Route path="lessons/:id" element={<LessonPage />} />
            <Route path="leaderboard" element={<LeaderboardPage />} />
            <Route path="profile" element={<StudentProfilePage />} />
            <Route path="students/:userId" element={<StudentProfilePage />} />
            <Route
              path="children"
              element={
                <ParentRoute>
                  <ParentChildrenPage />
                </ParentRoute>
              }
            />
            <Route
              path="admin"
              element={
                <StaffRoute>
                  <AdminLayout />
                </StaffRoute>
              }
            >
              <Route index element={<AdminIndexPage />} />
              <Route
                path="users"
                element={
                  <PlatformAdminRoute>
                    <AdminUsersPage />
                  </PlatformAdminRoute>
                }
              />
              <Route
                path="groups"
                element={
                  <PlatformAdminRoute>
                    <AdminGroupsPage />
                  </PlatformAdminRoute>
                }
              />
              <Route
                path="badges"
                element={
                  <PlatformAdminRoute>
                    <AdminBadgesPage />
                  </PlatformAdminRoute>
                }
              />
              <Route path="courses" element={<AdminCoursesPage />} />
              <Route path="courses/:courseId/lessons" element={<AdminLessonsPage />} />
              <Route path="lessons/:lessonId/edit" element={<AdminLessonEditPage />} />
              <Route path="lessons/:lessonId/tasks/new" element={<AdminTaskEditPage />} />
              <Route path="lessons/:lessonId/tasks/:taskId/edit" element={<AdminTaskEditPage />} />
              <Route path="submissions" element={<AdminSubmissionsPage />} />
              <Route path="parents" element={<AdminParentsPage />} />
            </Route>
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
      </ToastProvider>
    </AuthProvider>
  );
}
