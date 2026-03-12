import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Newspaper, TrendingUp, TrendingDown, Minus } from 'lucide-react';

export const SentimentComponent = ({ ticker }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!ticker) return;

    let cancelled = false;
    const fetchSentiment = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await axios.get(`/api/sentiment/${ticker}`);
        if (!cancelled) {
          setData(res.data);
        }
      } catch (err) {
        if (!cancelled) {
          setError('Failed to analyze news sentiment');
          console.error(err);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    fetchSentiment();

    return () => {
      cancelled = true;
    };
  }, [ticker]);

  if (!ticker) return null;

  return (
    <div className="p-3 flex flex-col gap-2">
      <div className="flex items-center gap-1.5 mb-1">
         <Newspaper size={14} className="text-purple-400" />
         <h2 className="text-xs font-semibold text-gray-300 uppercase tracking-wider">News Sentiment</h2>
      </div>

      {loading ? (
        <div className="animate-pulse flex space-x-4">
          <div className="flex-1 space-y-4 py-1">
            <div className="h-4 bg-gray-700 rounded w-full"></div>
            <div className="h-4 bg-gray-700 rounded w-5/6"></div>
          </div>
        </div>
      ) : error ? (
        <div className="text-sm text-red-400 p-2 bg-red-900/20 rounded border border-red-700/50">
          {error}
        </div>
      ) : data ? (
        <div className="flex flex-col gap-2">
             <div className="flex items-center gap-2">
                 <p className="text-xs text-gray-500 uppercase tracking-wide">Score:</p>
                 <div className="flex items-center gap-1">
                     {data.score === 'Bullish' && <TrendingUp size={16} className="text-green-400"/>}
                     {data.score === 'Bearish' && <TrendingDown size={16} className="text-red-400"/>}
                     {data.score === 'Neutral' && <Minus size={16} className="text-gray-400"/>}
                     <span className={`text-sm font-bold ${data.score === 'Bullish' ? 'text-green-400' : data.score === 'Bearish' ? 'text-red-400' : 'text-gray-200'}`}>
                         {data.score}
                     </span>
                 </div>
             </div>
             <div>
                 <p className="text-[12px] text-gray-300 leading-snug italic border-l-2 border-purple-500/50 pl-2">
                     "{data.summary}"
                 </p>
             </div>
        </div>
      ) : null}
    </div>
  );
};
