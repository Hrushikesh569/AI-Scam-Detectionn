import React from 'react';

const ScoreBar = ({ label, score, colorClass = "bg-slate-400" }) => {
  return (
    <div className="mb-4">
      <div className="flex justify-between mb-1 text-sm font-medium">
        <span className="text-slate-300">{label}</span>
        <span className="text-slate-100">{score}%</span>
      </div>
      <div className="w-full bg-slate-800 rounded-full h-2.5 overflow-hidden shadow-inner flex">
        <div 
          className={`h-2.5 rounded-full transition-all duration-1000 ease-out ${colorClass}`} 
          style={{ width: `${score}%` }}
        ></div>
      </div>
    </div>
  );
};

export default ScoreBar;
