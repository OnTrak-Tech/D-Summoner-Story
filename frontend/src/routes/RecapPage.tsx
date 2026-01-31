import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useRecapData } from '../hooks/recapHooks';
import { RecapViewer } from '../components/RecapViewer';
import { apiService } from '../services/api';

export const RecapPage: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();

  const { data: recapData, isLoading, isError, error } = useRecapData(sessionId || null);

  const handleShare = async () => {
    if (!recapData) return;
    try {
      const shareRes = await apiService.generateShareLink(recapData.session_id);
      if (navigator.share) {
        await navigator.share({
          title: `OnTrak: ${recapData.summoner_name}'s Story`,
          text: shareRes.preview_text,
          url: shareRes.share_url,
        });
      } else {
        await navigator.clipboard.writeText(shareRes.share_url);
        alert('Link copied!');
      }
    } catch (e) {
      console.error(e);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-brand-dark flex items-center justify-center">
        <div className="animate-spin text-4xl">⏳</div>
      </div>
    );
  }

  if (isError || !recapData) {
    return (
      <div className="min-h-screen bg-brand-dark flex items-center justify-center p-6 text-white">
        <div className="text-center">
          <h2 className="text-3xl font-bold mb-4">Recap Not Found</h2>
          <p className="text-slate-400 mb-8">{error?.message || "We couldn't find this recap."}</p>
          <button
            onClick={() => navigate('/')}
            className="px-6 py-3 bg-brand-vibrant rounded-lg font-bold"
          >
            Create New Recap
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-brand-dark py-12 px-4">
      <RecapViewer recapData={recapData} onShare={handleShare} onStartNew={() => navigate('/')} />
    </div>
  );
};
