import React from 'react';
import { AlertCircle, AlertTriangle, Info, CheckCircle } from 'lucide-react';

const ExplanationPanel = ({ explanations, riskLevel }) => {

  const getIcon = () => {
    switch(riskLevel) {
      case 'Scam': return <AlertCircle className="text-rose-400 w-5 h-5 flex-shrink-0 mt-0.5" />;
      case 'Suspicious': return <AlertTriangle className="text-amber-400 w-5 h-5 flex-shrink-0 mt-0.5" />;
      case 'Safe': return <CheckCircle className="text-emerald-400 w-5 h-5 flex-shrink-0 mt-0.5" />;
      default: return <Info className="text-slate-400 w-5 h-5 flex-shrink-0 mt-0.5" />;
    }
  };

  if (!explanations || explanations.length === 0) return null;

  return (
    <div className="mt-6 p-4 rounded-xl bg-slate-800/50 border border-slate-700/50 shadow-inner">
      <h4 className="text-sm font-semibold text-slate-300 mb-3 tracking-wide uppercase">AI Analysis Breakdown</h4>
      <ul className="space-y-3">
        {explanations.map((exp, index) => (
          <li key={index} className="flex gap-3 text-sm text-slate-200">
            {getIcon()}
            <span className="leading-relaxed">{exp}</span>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default ExplanationPanel;
