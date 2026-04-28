import React, { useState } from 'react';
import InputBox from './components/InputBox';
import ResultCard from './components/ResultCard';
import { Shield } from 'lucide-react';

function App() {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState(null);

  const analyzeMessage = async (text) => {
    setIsAnalyzing(true);
    setResult(null); // clear previous results

    try {
      const response = await fetch("http://localhost:8000/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: text,
          unknown_sender: true, // We can simulate unknown sender as true for now, or add a checkbox later
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to analyze message");
      }

      const data = await response.json();

      setResult({
        riskLevel: data.label,
        overallScore: data.final_score,
        scores: data.breakdown,
        explanations: data.explanation,
      });
    } catch (error) {
      console.error(error);
      alert("Error connecting to backend API. Is it running?");
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 relative overflow-x-hidden selection:bg-emerald-500/30">
      {/* Background gradients */}
      <div className="absolute top-0 inset-x-0 h-[500px] bg-gradient-to-b from-emerald-900/20 via-slate-900/5 to-transparent pointer-events-none"></div>
      
      <main className="relative z-10 container mx-auto px-4 py-16 sm:py-24 flex flex-col items-center">
        
        {/* Header Section */}
        <div className="text-center mb-12 animate-fade-in-down">
          <div className="flex justify-center mb-6">
            <div className="p-4 bg-slate-900/50 rounded-2xl border border-slate-800 shadow-xl backdrop-blur-sm relative">
               <div className="absolute inset-0 bg-emerald-500/20 blur-xl rounded-full"></div>
               <Shield className="w-12 h-12 text-emerald-400 relative z-10" />
            </div>
          </div>
          <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight mb-4 text-transparent bg-clip-text bg-gradient-to-r from-slate-100 via-slate-300 to-slate-500">
            Scam Detection AI
          </h1>
          <p className="text-lg text-slate-400 max-w-xl mx-auto font-light">
            Detect scam messages using Real-time AI + Behavioral Intelligence. Paste a suspicious message to begin analysis.
          </p>
        </div>

        {/* Input Component */}
        <div className="w-full relative z-20">
          <InputBox onAnalyze={analyzeMessage} isAnalyzing={isAnalyzing} />
        </div>

        {/* Result Post-Analysis Component */}
        <div className="w-full relative z-10 transition-all duration-500">
          <ResultCard result={result} />
        </div>

      </main>
      
      {/* Footer */}
      <footer className="absolute bottom-6 w-full text-center text-sm text-slate-600">
        AI Scam Detection System &bull; Behavioral Context Engine
      </footer>
    </div>
  );
}

export default App;
