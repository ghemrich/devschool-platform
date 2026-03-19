import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import CoursesPage from './pages/CoursesPage';
import CourseDetailPage from './pages/CourseDetailPage';
import DashboardPage from './pages/DashboardPage';
import AdminPage from './pages/admin/AdminPage';
import AdminCoursesPage from './pages/admin/AdminCoursesPage';
import AdminUsersPage from './pages/admin/AdminUsersPage';
import AdminPromotionPage from './pages/admin/AdminPromotionPage';
import MentorDashboardPage from './pages/MentorDashboardPage';
import VerifyPage from './pages/VerifyPage';

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/courses" element={<CoursesPage />} />
        <Route path="/courses/:id" element={<CourseDetailPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/admin" element={<AdminPage />} />
        <Route path="/admin/courses" element={<AdminCoursesPage />} />
        <Route path="/admin/users" element={<AdminUsersPage />} />
        <Route path="/admin/promotion" element={<AdminPromotionPage />} />
        <Route path="/mentor" element={<MentorDashboardPage />} />
        <Route path="/verify/:id" element={<VerifyPage />} />
      </Route>
    </Routes>
  );
}
