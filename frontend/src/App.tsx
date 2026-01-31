import React from 'react';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from './api/queryClient';
import { ErrorBoundary } from './components/ErrorBoundary';
import { AuthProvider } from './contexts/AuthContext';

// Pages
import { Landing, Auth, Connect, Dashboard } from './pages';

// Styles
import './index.css';

// Error fallback component
const ErrorFallback: React.FC = () => (
  <div className="min-h-screen bg-gray-900 flex items-center justify-center text-white">
    <div className="text-center">
      <h1 className="text-4xl font-bold mb-4">Oops!</h1>
      <p className="text-gray-400 mb-6">Something went wrong.</p>
      <a href="/" className="px-4 py-2 bg-purple-600 rounded-lg hover:bg-purple-500">
        Go Home
      </a>
    </div>
  </div>
);

const router = createBrowserRouter([
  {
    path: '/',
    element: <Landing />,
    errorElement: <ErrorFallback />,
  },
  {
    path: '/auth',
    element: <Auth />,
    errorElement: <ErrorFallback />,
  },
  {
    path: '/connect',
    element: <Connect />,
    errorElement: <ErrorFallback />,
  },
  {
    path: '/dashboard',
    element: <Dashboard />,
    errorElement: <ErrorFallback />,
  },
]);

const App: React.FC = () => {
  return (
    <React.StrictMode>
      <ErrorBoundary
        onError={(error, errorInfo) => {
          console.error('System Error:', error, errorInfo);
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
