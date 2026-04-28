import React, { useState } from 'react';
import { Search, Loader2 } from 'lucide-react';

const InputBox = ({ onAnalyze, isAnalyzing }) => {
  const [text, setText] = useState('');
  const [error, setError] = useState('');

  const handleAnalyze = () => {
    if (!text.trim()) {
      setError('Please enter a message to analyze.');
      return;
    }
    setError('');
    onAnalyze(text);
  };

  return (
    <div className="w-full max-w-2xl mx-auto backdrop-blur-md bg-slate-900/80 rounded-3xl p-6 shadow-2xl border border-slate-700/60 relative overflow-hidden">
      {/* Decorative gradient blur */}
      <div className="absolute -top-24 -right-24 w-48 h-48 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none"></div>
      <div className="absolute -bottom-24 -left-24 w-48 h-48 bg-blue-500/10 rounded-full blur-3xl pointer-events-none"></div>

      <div className="relative z-10">
        <label className="block text-slate-300 font-medium mb-3 ml-1 text-sm">
          Paste suspicious message below:
        </label>
        
        <div className="relative group">
          <textarea
            value={text}
            onChange={(e) => {
              setText(e.target.value);
              if (error) setError('');
            }}
            placeholder="e.g. URGENT: Your account has been locked. Click here to verify your identity..."
            className={`w-full h-40 bg-slate-950/50 text-slate-100 rounded-2xl p-4 pr-4 border resize-none focus:outline-none transition-all duration-300
              ${error ? 'border-rose-500/50 focus:border-rose-500 bg-rose-500/5' : 'border-slate-700 focus:border-emerald-500/50 hover:border-slate-600'}
              placeholder:text-slate-600 font-mono text-sm shadow-inner`}
            spellCheck="false"
          />
          {error && <p className="text-rose-400 text-xs mt-2 ml-1 animate-pulse">{error}</p>}
        </div>

        <div className="mt-6 flex justify-end">
          <button
            onClick={handleAnalyze}
            disabled={isAnalyzing}
            className={`flex items-center gap-2 px-6 py-3 rounded-xl font-medium text-sm transition-all duration-300 shadow-lg
              ${isAnalyzing 
                ? 'bg-slate-800 text-slate-400 cursor-not-allowed border border-slate-700' 
                : 'bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 text-white hover:shadow-[0_0_20px_-5px_rgba(16,185,129,0.5)] transform hover:-translate-y-0.5'
              }`}
          >
            {isAnalyzing ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Analyzing Context...
              </>
            ) : (
              <>
                <Search className="w-4 h-4" />
                Analyze Message
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default InputBox;
