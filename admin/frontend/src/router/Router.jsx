import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import MainLayout from '../layouts/MainLayout';
import UserQueryDataAnalysis from '../pages/UserQueryDataAnalysis';
import UserStatistics from '../pages/UserStatistics';
import TrafficInquiry from '../pages/TrafficInquiry';
import UsageCostInquiry from '../pages/UsageCostInquiry';

// --- 새로 추가 ---
import LoginPage from '../pages/Login';
import ProtectedRoute from './ProtectedRoute';
// --- ---

const router = createBrowserRouter([
  {
    path: 'login', // '/admin/login' 경로
    element: <LoginPage />,
  },
  {
    path: '/', // '/admin/' 이하 모든 경로
    element: (
      <ProtectedRoute> {/* <--- 보호막 적용 */}
        <MainLayout />
      </ProtectedRoute>
    ),
    children: [
      { path: '', element: <UserQueryDataAnalysis /> },
      { path: 'statistics', element: <UserStatistics /> },
      { path: 'traffic', element: <TrafficInquiry /> },
      { path: 'cost', element: <UsageCostInquiry /> },
    ],
  },
], 
  {
    basename: "/admin/"
  }
);

const Router = () => {
  return <RouterProvider router={router} />;
};

export default Router;