import React from 'react';
import { useRouteError, isRouteErrorResponse, useNavigate } from 'react-router-dom';

export const ErrorPage: React.FC = () => {
  const error = useRouteError();
  const navigate = useNavigate();

  let errorMessage = 'An unexpected error has occurred.';

  if (isRouteErrorResponse(error)) {
    // Handle router errors (404, etc)
    errorMessage = error.statusText || error.data?.message || errorMessage;
    if (error.status === 404) {
      errorMessage = 'Page not found.';
    }
  } else if (error instanceof Error) {
    // Handle thrown errors
    errorMessage = error.message;
  } else if (typeof error === 'string') {
    errorMessage = error;
  }

  return (
    <div className="min-h-screen bg-brand-dark flex items-center justify-center p-6 text-white">
      <div className="max-w-lg w-full bg-brand-secondary/80 backdrop-blur-xl border border-brand-vibrant/20 rounded-3xl p-10 shadow-2xl text-center">
        <div className="w-20 h-20 mx-auto mb-6 bg-brand-vibrant/10 rounded-full flex items-center justify-center border border-brand-vibrant/20">
          <span className="text-3xl">⚠️</span>
        </div>
        <h1 className="text-3xl font-black uppercase tracking-tighter mb-4 italic">Oops!</h1>
        <p className="text-slate-400 mb-8">{errorMessage}</p>

        <div className="flex gap-4 justify-center">
          <button
            onClick={() => navigate('/')}
            className="px-6 py-3 bg-brand-vibrant rounded-xl font-bold hover:bg-brand-deep transition-all"
          >
            Go Home
          </button>
          <button
            onClick={() => window.location.reload()}
            className="px-6 py-3 bg-white/5 border border-white/10 rounded-xl font-bold hover:bg-white/10 transition-all"
          >
            Reload
          </button>
        </div>
      </div>
    </div>
  );
};
