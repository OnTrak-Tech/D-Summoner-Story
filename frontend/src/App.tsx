import React from 'react';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from './api/queryClient';
import { ErrorBoundary } from './components/ErrorBoundary';
import { AuthProvider } from './contexts/AuthContext';

// Pages
import { Landing, Auth, Connect, Dashboard } from './pages';

// Legacy Routes (for backward compatibility)
import { LoadingPage } from './routes/LoadingPage';
import { RecapPage } from './routes/RecapPage';
import { ErrorPage } from './routes/ErrorPage';

// Styles
import './index.css';

const router = createBrowserRouter([
  // New MVP Routes
  {
    path: '/',
    element: <Landing />,
    errorElement: <ErrorPage />,
  },
  {
    path: '/auth',
    element: <Auth />,
    errorElement: <ErrorPage />,
  },
  {
    path: '/connect',
    element: <Connect />,
    errorElement: <ErrorPage />,
  },
  {
    path: '/dashboard',
    element: <Dashboard />,
    errorElement: <ErrorPage />,
  },
  // Legacy Routes (backward compatibility)
  {
    path: '/loading/:platform/:region/:summonerName',
    element: <LoadingPage />,
    errorElement: <ErrorPage />,
  },
  {
    path: '/recap/:sessionId',
    element: <RecapPage />,
    errorElement: <ErrorPage />,
  },
  {
    path: '/recap/:timeframe',
    element: <RecapPage />,
    errorElement: <ErrorPage />,
  },
]);

const App: React.FC = () => {
  return (
    <React.StrictMode>
      <ErrorBoundary
        onError={(error, errorInfo) => {
          console.error('OnTrak System Error:', error, errorInfo);
        }}
      >
        <AuthProvider>
          <QueryClientProvider client={queryClient}>
            <RouterProvider router={router} />
          </QueryClientProvider>
        </AuthProvider>
      </ErrorBoundary>
    </React.StrictMode>
  );
};

export default App;
