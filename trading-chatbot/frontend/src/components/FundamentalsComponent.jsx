import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Activity, ShieldCheck, AlertTriangle } from 'lucide-react';

export const FundamentalsComponent = ({ ticker }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!ticker) return;

    let cancelled = false;
    const fetchFundamentals = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await axios.get(`/api/fundamentals/${ticker}`);
        if (!cancelled) {
          setData(res.data);
        }
      } catch (err) {
        if (!cancelled) {
          setError('Failed to load fundamentals');
          console.error(err);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    fetchFundamentals();

    return () => {
      cancelled = true;
    };
  }, [ticker]);

  if (!ticker) return null;

  return (
    <div className="bg-[#151924] rounded-xl border border-gray-800 p-4 mb-4 shadow-xl">
      <div className="flex items-center gap-2 mb-4 border-b border-gray-800 pb-2">
         <Activity size={16} className="text-blue-400" />
         <h2 className="text-sm font-semibold text-gray-200 uppercase tracking-wider">Fundamentals & Health</h2>
      </div>

      {loading ? (
        <div className="animate-pulse flex space-x-4">
          <div className="flex-1 space-y-4 py-1">
            <div className="h-4 bg-gray-700 rounded w-3/4"></div>
            <div className="space-y-2">
              <div className="h-4 bg-gray-700 rounded"></div>
              <div className="h-4 bg-gray-700 rounded w-5/6"></div>
            </div>
          </div>
        </div>
      ) : error ? (
        <div className="text-sm text-red-400 p-2 bg-red-900/20 rounded border border-red-700/50">
          {error}
        </div>
      ) : data ? (
        <div className="space-y-4">
          {/* Key Metrics Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
             <div className="bg-gray-800 p-3 rounded-lg border border-gray-700">
                <p className="text-xs text-gray-500 uppercase">Score</p>
                <p className={`text-lg font-bold ${data.score > 70 ? 'text-green-400' : data.score > 40 ? 'text-yellow-400' : 'text-red-400'}`}>
                   {data.score.toFixed(1)}/100
                </p>
             </div>
             <div className="bg-gray-800 p-3 rounded-lg border border-gray-700">
                <p className="text-xs text-gray-500 uppercase">P/E Ratio</p>
                <p className="text-lg font-bold text-gray-200">
                   {data.metrics?.pe_ratio !== undefined ? data.metrics.pe_ratio.toFixed(1) : '--'}
                </p>
             </div>
             <div className="bg-gray-800 p-3 rounded-lg border border-gray-700">
                <p className="text-xs text-gray-500 uppercase">ROE</p>
                <p className="text-lg font-bold text-gray-200">
                   {data.metrics?.roe !== undefined ? `${data.metrics.roe.toFixed(1)}%` : '--'}
                </p>
             </div>
             <div className="bg-gray-800 p-3 rounded-lg border border-gray-700">
                <p className="text-xs text-gray-500 uppercase">D/E Ratio</p>
                <p className="text-lg font-bold text-gray-200">
                   {data.metrics?.debt_to_equity !== undefined ? data.metrics.debt_to_equity.toFixed(2) : '--'}
                </p>
             </div>
          </div>

          {/* Qualitative insights */}
          {((data.strengths && data.strengths.length > 0) || (data.risks && data.risks.length > 0)) && (
            <div className="grid md:grid-cols-2 gap-4 mt-4 text-sm">
                {data.strengths && data.strengths.length > 0 && (
                    <div className="space-y-2">
                        <h3 className="flex items-center gap-1 text-green-400 font-medium">
                            <ShieldCheck size={14} /> Strengths
                        </h3>
                        <ul className="list-disc leading-relaxed list-inside text-gray-400 space-y-1">
                            {data.strengths.map((str, i) => <li key={i}>{str}</li>)}
                        </ul>
                    </div>
                )}
                {data.risks && data.risks.length > 0 && (
                    <div className="space-y-2">
                        <h3 className="flex items-center gap-1 text-yellow-500 font-medium">
                            <AlertTriangle size={14} /> Key Risks
                        </h3>
                        <ul className="list-disc leading-relaxed list-inside text-gray-400 space-y-1">
                            {data.risks.map((risk, i) => <li key={i}>{risk}</li>)}
                        </ul>
                    </div>
                )}
            </div>
          )}
        </div>
      ) : (
         <div className="text-sm text-gray-500">No fundamental data available for {ticker}.</div>
      )}
    </div>
  );
};
