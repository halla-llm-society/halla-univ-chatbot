// src/router/Router.jsx

import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import MainLayout from '../layouts/MainLayout';
import UserQueryDataAnalysis from '../pages/UserQueryDataAnalysis';
import UserStatistics from '../pages/UserStatistics';
import TrafficInquiry from '../pages/TrafficInquiry';
import UsageCostInquiry from '../pages/UsageCostInquiry';

const router = createBrowserRouter([
  {
    path: '/',
    element: <MainLayout />, // 레이어 걸어두기
    children: [
      { path: '', element: <UserQueryDataAnalysis /> }, // 기본 페이지
      { path: '/statistics', element: <UserStatistics /> }, // /statistics 주소로 오면 이 페이지
      { path: '/traffic', element: <TrafficInquiry /> }, // /traffic 주소로 오면 이 페이지
      { path: '/cost', element: <UsageCostInquiry /> }, // /cost 주소로 오면 이 페이지
    ],
  },
], 
  {
    basename: "/admin"
  }
);

const Router = () => {
  return <RouterProvider router={router} />;
};

export default Router;
