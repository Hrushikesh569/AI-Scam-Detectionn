import React, { useEffect, useState } from 'react';
import ScoreBar from './ScoreBar';
import ExplanationPanel from './ExplanationPanel';
import { ShieldCheck, ShieldAlert, AlertOctagon } from 'lucide-react';

const ResultCard = ({ result }) => {
  const [animate, setAnimate] = useState(false);

  useEffect(() => {
    // Small delay to trigger mount animations
    let timer;
    if (result) {
      setAnimate(false);
      timer = setTimeout(() => setAnimate(true), 50);
    }
    return () => clearTimeout(timer);
  }, [result]);

  if (!result) return null;

  const { overallScore, riskLevel, scores, explanations } = result;

  const getConfig = () => {
    switch (riskLevel) {
      case 'Safe':
        return {
          colorClass: 'text-emerald-400',
          bgClass: 'bg-emerald-400/10',
          borderClass: 'border-emerald-500/30',
          icon: <ShieldCheck className="w-10 h-10 text-emerald-400" />,
          barColor: 'bg-emerald-500',
          shadow: 'shadow-[0_0_30px_-5px_rgba(16,185,129,0.3)]'
        };
      case 'Suspicious':
        return {
          colorClass: 'text-amber-400',
          bgClass: 'bg-amber-400/10',
          borderClass: 'border-amber-500/30',
          icon: <ShieldAlert className="w-10 h-10 text-amber-400" />,
          barColor: 'bg-amber-500',
          shadow: 'shadow-[0_0_30px_-5px_rgba(245,158,11,0.3)]'
        };
      case 'Scam':
        return {
          colorClass: 'text-rose-500',
          bgClass: 'bg-rose-500/10',
          borderClass: 'border-rose-500/30',
          icon: <AlertOctagon className="w-10 h-10 text-rose-500" />,
          barColor: 'bg-rose-500',
          shadow: 'shadow-[0_0_30px_-5px_rgba(244,63,94,0.3)]'
        };
      default:
        return {
          colorClass: 'text-slate-400',
          bgClass: 'bg-slate-800',
          borderClass: 'border-slate-700',
          icon: null,
          barColor: 'bg-slate-500',
          shadow: ''
        };
    }
  };

  const config = getConfig();

  return (
    <div 
      className={`mt-8 max-w-2xl mx-auto w-full rounded-2xl border ${config.borderClass} bg-slate-900/60 backdrop-blur-md p-6 sm:p-8 overflow-hidden transition-all duration-700 ease-out transform ${animate ? 'opacity-100 translate-y-0 scale-100' : 'opacity-0 translate-y-4 scale-95'} ${config.shadow}`}
    >
      <div className="flex items-center gap-4 mb-8">
        <div className={`p-3 rounded-full ${config.bgClass}`}>
          {config.icon}
        </div>
        <div>
          <h2 className="text-sm font-semibold text-slate-400 tracking-wider uppercase mb-1">Analysis Result</h2>
          <div className="flex items-baseline gap-3">
            <span className={`text-3xl font-bold tracking-tight ${config.colorClass}`}>
              {riskLevel}
            </span>
            <span className="text-lg font-medium text-slate-300">
              Score: {overallScore}/100
            </span>
          </div>
        </div>
      </div>

      <div className="space-y-6">
        <div>
          <h3 className="text-lg font-medium text-slate-200 mb-4 border-b border-slate-800 pb-2">Score Breakdown</h3>
          <div className="space-y-4">
            <ScoreBar label="Text Risk Score" score={animate ? scores.text : 0} colorClass={config.barColor} />
            <ScoreBar label="Urgency Score" score={animate ? scores.urgency : 0} colorClass={config.barColor} />
            <ScoreBar label="Psychological Score" score={animate ? scores.psychological : 0} colorClass={config.barColor} />
            <ScoreBar label="Behavior Score" score={animate ? scores.behavior : 0} colorClass={config.barColor} />
          </div>
        </div>

        <ExplanationPanel explanations={explanations} riskLevel={riskLevel} />
      </div>
    </div>
  );
};

export default ResultCard;
