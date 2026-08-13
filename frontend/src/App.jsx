import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Loader2, FileDown, Sparkles, CheckCircle2, RefreshCw, Check, ArrowRight, KeyRound, ExternalLink, X } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

// Use Vite env var for production, fallback to localhost for dev
const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

const markdownComponents = {
  h1: ({ node, ...props }) => <h1 className="text-2xl font-bold text-crimson mt-4 mb-2" {...props} />,
  h2: ({ node, ...props }) => <h2 className="text-xl font-bold text-crimson mt-4 mb-2" {...props} />,
  h3: ({ node, ...props }) => <h3 className="text-lg font-bold text-offwhite mt-3 mb-1" {...props} />,
  p: ({ node, ...props }) => <p className="text-sm text-offwhite/80 leading-relaxed mb-2" {...props} />,
  ul: ({ node, ...props }) => <ul className="list-disc pl-5 text-sm text-offwhite/80 space-y-1 mb-2" {...props} />,
  ol: ({ node, ...props }) => <ol className="list-decimal pl-5 text-sm text-offwhite/80 space-y-1 mb-2" {...props} />,
  li: ({ node, ...props }) => <li {...props} />,
  strong: ({ node, ...props }) => <strong className="font-bold text-offwhite" {...props} />,
  a: ({ node, ...props }) => <a className="text-crimson underline hover:text-crimson/80" target="_blank" rel="noreferrer" {...props} />,
};

function App() {
  const [topic, setTopic] = useState('');
  const [duration, setDuration] = useState(30);

  const [isLoading, setIsLoading] = useState(false);
  const [loadingStage, setLoadingStage] = useState('');
  const [stage, setStage] = useState('input');

  const [threadId, setThreadId] = useState(null);
  const [draftPlan, setDraftPlan] = useState('');
  const [refinedPlan, setRefinedPlan] = useState('');
  const [claims, setClaims] = useState([]);
  const [customText, setCustomText] = useState('');

  const [selectedClaims, setSelectedClaims] = useState([]);
  const [slides, setSlides] = useState([]);
  const [logs, setLogs] = useState([]);

  // API Key State
  const [apiKey, setApiKey] = useState(localStorage.getItem('groq_api_key') || '');
  const [showApiKeyModal, setShowApiKeyModal] = useState(false);
  const [tempApiKey, setTempApiKey] = useState('');

  // Check for API key on initial load
  useEffect(() => {
    if (!apiKey) {
      setShowApiKeyModal(true);
    }
  }, [apiKey]);

  const handleSaveApiKey = () => {
    if (tempApiKey.trim()) {
      localStorage.setItem('groq_api_key', tempApiKey.trim());
      setApiKey(tempApiKey.trim());
      setShowApiKeyModal(false);
      setTempApiKey('');
    }
  };

  const handleStart = async (e) => {
    if (e) e.preventDefault();
    if (!apiKey) { 
      setShowApiKeyModal(true); 
      return; 
    }
    
    setIsLoading(true);
    setLoadingStage('Researching & Extracting Claims...');
    try {
      const res = await fetch(`${API_BASE}/start-graph`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'X-Groq-Key': apiKey
        },
        body: JSON.stringify({ topic, lecture_duration: parseInt(duration) })
      });
      const data = await res.json();
      setThreadId(data.thread_id);
      setDraftPlan(data.draft_plan);
      setClaims(data.extracted_claims);
      setStage('review_1');
    } catch (error) {
      console.error("Error starting graph:", error);
    }
    setIsLoading(false);
  };

  const handleResumeHITL1 = async (decision) => {
    setIsLoading(true);
    setLoadingStage('Refining Plan...');
    try {
      const res = await fetch(`${API_BASE}/resume-graph`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'X-Groq-Key': apiKey
        },
        body: JSON.stringify({ thread_id: threadId, human_decision: decision, custom_text: customText })
      });
      const data = await res.json();

      if (data.next_stage === 'review_2') {
        setRefinedPlan(data.refined_plan);
        setSelectedClaims(data.extracted_claims);
        setStage('review_2');
      } else {
        setDraftPlan(data.draft_plan);
        setStage('review_1');
      }
      setCustomText('');
    } catch (error) {
      console.error("Error resuming graph:", error);
    }
    setIsLoading(false);
  };

  const handleResumeHITL2 = async () => {
    setIsLoading(true);
    setLoadingStage('Generating Slides...');
    try {
      const res = await fetch(`${API_BASE}/resume-graph`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'X-Groq-Key': apiKey
        },
        body: JSON.stringify({ thread_id: threadId, verified_claims: selectedClaims })
      });
      const data = await res.json();
      setSlides(data.final_brief?.slides || []);
      setLogs(data.logs || []);
      setStage('final');
    } catch (error) {
      console.error("Error resuming graph:", error);
    }
    setIsLoading(false);
  };

  const handleDownload = async () => {
    try {
      const res = await fetch(`${API_BASE}/download-pptx`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'X-Groq-Key': apiKey
        },
        body: JSON.stringify({ thread_id: threadId })
      });
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `lecture_deck.pptx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (error) {
      console.error("Download failed:", error);
    }
  };

  const toggleClaim = (claim) => {
    setSelectedClaims(prev =>
      prev.includes(claim) ? prev.filter(c => c !== claim) : [...prev, claim]
    );
  };

  return (
    <div className="min-h-screen bg-black text-offwhite flex flex-col md:flex-row overflow-hidden">

      {/* API KEY MODAL */}
      <AnimatePresence>
        {showApiKeyModal && (
          <motion.div 
            initial={{opacity: 0}} 
            animate={{opacity: 1}} 
            exit={{opacity: 0}}
            className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          >
            <motion.div 
              initial={{scale: 0.9, y: 20}} 
              animate={{scale: 1, y: 0}} 
              exit={{scale: 0.9, y: 20}}
              className="bg-darkgray border border-crimson/40 rounded-2xl p-8 max-w-md w-full shadow-2xl relative"
            >
              {/* Close Button */}
              <button 
                onClick={() => setShowApiKeyModal(false)}
                className="absolute top-4 right-4 p-2 text-offwhite/50 hover:text-crimson transition"
                title="Close"
              >
                <X size={20} />
              </button>

              <div className="flex items-center gap-3 mb-6">
                <div className="p-3 bg-crimson/20 rounded-xl">
                  <KeyRound className="text-crimson" size={24} />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-offwhite">Groq API Key Required</h2>
                  <p className="text-xs text-offwhite/60">Required to run the LangGraph agent</p>
                </div>
              </div>

              <p className="text-sm text-offwhite/70 mb-4">
                To generate slides, this app uses Groq's high-speed LLMs. Please enter your Groq API key to continue. Your key is stored locally in your browser and is only sent securely to the backend during processing.
              </p>

              <a 
                href="https://console.groq.com/keys" 
                target="_blank" 
                rel="noreferrer" 
                className="text-crimson underline hover:text-crimson/80 text-sm mb-4 inline-flex items-center gap-1"
              >
                Get your free Groq API key here <ExternalLink size={14} />
              </a>

              <input 
                type="password" 
                value={tempApiKey}
                onChange={(e) => setTempApiKey(e.target.value)}
                className="w-full p-3 rounded-xl bg-black border border-crimson/30 focus:outline-none focus:ring-1 focus:ring-crimson transition text-offwhite mb-4"
                placeholder="gsk_..."
                autoFocus
              />
              
              <button 
                onClick={handleSaveApiKey}
                className="w-full bg-crimson text-offwhite font-bold py-3 rounded-xl hover:opacity-90 transition flex items-center justify-center gap-2 shadow-lg shadow-crimson/20"
              >
                Save & Continue
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* LEFT PANEL */}
      <div className="w-full md:w-[380px] p-8 bg-darkgray shadow-2xl flex flex-col border-r border-crimson/20 h-screen sticky top-0 z-30">
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="mb-8 flex justify-between items-start">
          <div>
            {/* Changed to text-offwhite */}
            <h1 className="text-3xl font-bold mb-1 text-offwhite flex items-center gap-2">
              <Sparkles className="text-crimson" /> Lecture Agent
            </h1>
            <p className="text-sm opacity-60 text-offwhite">LangGraph + HITL + Groq</p>
          </div>
          <button 
            onClick={() => setShowApiKeyModal(true)}
            className="p-2 text-offwhite/40 hover:text-crimson transition"
            title="Change API Key"
          >
            <KeyRound size={18} />
          </button>
        </motion.div>

        <div className="flex-1 overflow-y-auto pr-2 custom-scroll">
          {isLoading ? (
            <div className="h-full flex flex-col items-center justify-center gap-4">
              <Loader2 className="w-12 h-12 text-crimson animate-spin" />
              <p className="text-crimson font-medium text-center px-4">{loadingStage}</p>
            </div>
          ) : (
            <AnimatePresence mode="wait">
              {stage === 'input' && (
                <motion.form key="input" onSubmit={handleStart} className="flex flex-col gap-5" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 20 }}>
                  <label className="flex flex-col gap-2">
                    <span className="font-semibold text-crimson text-sm uppercase tracking-wide">Lecture Topic</span>
                    <input 
                      type="text" 
                      value={topic}
                      onChange={(e) => setTopic(e.target.value)}
                      className="p-4 rounded-xl bg-black border border-crimson/30 focus:outline-none focus:ring-1 focus:ring-crimson transition text-offwhite"
                      placeholder="e.g., Intro to Quantum Computing"
                      required
                    />
                  </label>

                  <label className="flex flex-col gap-2">
                    <span className="font-semibold text-crimson text-sm uppercase tracking-wide">Duration (mins)</span>
                    <input 
                      type="number" 
                      min="1"
                      value={duration}
                      onChange={(e) => setDuration(e.target.value)}
                      className="p-4 rounded-xl bg-black border border-crimson/30 focus:outline-none focus:ring-1 focus:ring-crimson transition text-offwhite"
                      placeholder="e.g., 45"
                      required
                    />
                  </label>

                  <button type="submit" className="bg-crimson text-offwhite font-bold py-4 rounded-xl hover:opacity-90 transition flex items-center justify-center gap-2 shadow-lg shadow-crimson/20 mt-4">
                    Start Research
                  </button>
                </motion.form>
              )}

              {stage === 'final' && (
                <motion.div key="final" className="flex flex-col gap-4" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }}>
                  <div className="bg-black/50 p-4 rounded-2xl border border-crimson/20 shadow-inner mb-2">
                    <button onClick={handleDownload} className="w-full bg-crimson text-offwhite font-bold py-3 rounded-xl hover:opacity-90 transition flex items-center justify-center gap-2 shadow-lg shadow-crimson/20">
                      <FileDown size={20} /> Download .pptx
                    </button>
                  </div>

                  <div className="bg-black/50 p-4 rounded-2xl border border-crimson/20 shadow-inner">
                    <h3 className="font-bold text-crimson mb-3 text-sm flex items-center gap-2"><CheckCircle2 size={16} /> Process Trace</h3>
                    <div className="space-y-4 max-h-96 overflow-y-auto pr-2 custom-scroll">
                      {logs.map((log, i) => (
                        <div key={i} className="border-l-2 border-crimson pl-3">
                          <div className="font-bold text-crimson text-xs uppercase">{log.node}</div>
                          <div className="opacity-60 text-[10px] text-offwhite">{new Date(log.timestamp).toLocaleTimeString()}</div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <button onClick={() => { setStage('input'); setSlides([]); setLogs([]); setClaims([]); }} className="w-full bg-offwhite/10 hover:bg-offwhite/20 border border-offwhite/20 py-3 rounded-xl font-medium transition flex items-center justify-center gap-2 text-offwhite">
                    <RefreshCw size={16} /> New Lecture
                  </button>
                </motion.div>
              )}
            </AnimatePresence>
          )}
        </div>
      </div>

      {/* RIGHT PANEL */}
      <div className="flex-1 p-8 md:p-12 overflow-auto bg-black custom-scroll" style={{ height: "100vh" }}>
        <AnimatePresence mode="wait">

          {stage === 'input' && (
            <motion.div key="welcome" className="h-full flex items-center justify-center text-center" initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.5 }}>
              <div>
                {/* Changed to text-offwhite */}
                <h2 className="text-5xl font-bold text-offwhite mb-4 drop-shadow-lg">Slide Generator</h2>
                <p className="text-offwhite opacity-60 max-w-lg mx-auto text-lg">Enter a topic on the left to begin. The agent will research, extract claims, ask for your review, and generate a dynamic slide deck.</p>
              </div>
            </motion.div>
          )}

          {stage === 'review_1' && (
            <motion.div key="review_1" className="max-w-4xl mx-auto" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }}>
              {/* Changed to text-offwhite */}
              <h2 className="text-3xl font-bold text-offwhite mb-6">HITL 1: Plan Review</h2>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
                <div className="bg-darkgray p-6 rounded-2xl border border-crimson/20 shadow-xl">
                  <h3 className="font-bold text-crimson mb-4 text-lg">Draft Plan</h3>
                  <div className="text-sm text-offwhite/90">
                    <ReactMarkdown components={markdownComponents}>{draftPlan}</ReactMarkdown>
                  </div>
                </div>

                <div className="bg-darkgray p-6 rounded-2xl border border-crimson/20 shadow-xl">
                  <h3 className="font-bold text-crimson mb-4 text-lg">Extracted Claims ({claims.length})</h3>
                  <ul className="space-y-3 text-sm text-offwhite/80">
                    {claims.map((claim, i) => (
                      <li key={i} className="pb-3 border-b border-crimson/10 last:border-0">
                        <ReactMarkdown components={markdownComponents}>{claim}</ReactMarkdown>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              <div className="bg-darkgray p-6 rounded-2xl border border-crimson/20 shadow-xl">
                <h3 className="font-bold text-crimson mb-4 text-lg">Provide Feedback</h3>
                <textarea
                  value={customText}
                  onChange={(e) => setCustomText(e.target.value)}
                  className="w-full p-4 rounded-xl bg-black border border-crimson/30 focus:outline-none focus:ring-1 focus:ring-crimson transition text-offwhite text-sm mb-4 min-h-[100px]"
                  placeholder="Type custom instructions here (e.g., 'Make the intro shorter', 'Add a section on recent developments')..."
                />
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  <button onClick={() => handleResumeHITL1("Approve")} className="bg-crimson hover:bg-crimson/90 py-3 rounded-xl text-sm font-semibold transition shadow-md text-offwhite flex items-center justify-center gap-2">Approve & Verify <ArrowRight size={16} /></button>
                  <button onClick={() => handleResumeHITL1("Emphasize Examples")} className="bg-offwhite/10 hover:bg-offwhite/20 py-3 rounded-xl text-sm font-semibold transition shadow-md text-offwhite">Add Examples</button>
                  <button onClick={() => handleResumeHITL1("Emphasize Ethics")} className="bg-offwhite/10 hover:bg-offwhite/20 py-3 rounded-xl text-sm font-semibold transition shadow-md text-offwhite">Add Ethics</button>
                  <button onClick={() => handleResumeHITL1("More Sources")} className="bg-offwhite/10 hover:bg-offwhite/20 py-3 rounded-xl text-sm font-semibold transition shadow-md text-offwhite col-span-2 md:col-span-1">More Sources</button>
                  <button onClick={() => handleResumeHITL1("Rework")} className="bg-red-900/40 hover:bg-red-900/60 border border-crimson/40 py-3 rounded-xl text-sm font-semibold transition shadow-md text-offwhite col-span-2 md:col-span-2">Rework Plan (with instructions above)</button>
                </div>
              </div>
            </motion.div>
          )}

          {stage === 'review_2' && (
            <motion.div key="review_2" className="max-w-4xl mx-auto" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }}>
              {/* Changed to text-offwhite */}
              <h2 className="text-3xl font-bold text-offwhite mb-6">HITL 2: Fact Verification</h2>

              <div className="bg-darkgray p-6 rounded-2xl border border-crimson/20 shadow-xl mb-8">
                <h3 className="font-bold text-crimson mb-4 text-lg">Refined Plan</h3>
                <div className="text-sm text-offwhite/90">
                  <ReactMarkdown components={markdownComponents}>{refinedPlan}</ReactMarkdown>
                </div>
              </div>

              <div className="bg-darkgray p-6 rounded-2xl border border-crimson/20 shadow-xl">
                <h3 className="font-bold text-crimson mb-4 text-lg">Select Claims for Slides</h3>
                <div className="space-y-3">
                  {claims.map((claim, i) => (
                    <div
                      key={i}
                      onClick={() => toggleClaim(claim)}
                      className={`p-4 rounded-lg cursor-pointer flex items-start gap-3 transition border ${selectedClaims.includes(claim) ? 'bg-crimson/20 border-crimson text-offwhite' : 'bg-black/40 border-transparent text-offwhite/40'}`}
                    >
                      <div className={`mt-1 w-5 h-5 rounded-md flex items-center justify-center border ${selectedClaims.includes(claim) ? 'bg-crimson border-crimson' : 'border-offwhite/30'}`}>
                        {selectedClaims.includes(claim) && <Check className="w-4 h-4 text-offwhite" />}
                      </div>
                      <div className="flex-1 text-sm">
                        <ReactMarkdown components={markdownComponents}>{claim}</ReactMarkdown>
                      </div>
                    </div>
                  ))}
                </div>

                <button
                  onClick={handleResumeHITL2}
                  className="w-full mt-6 bg-crimson text-offwhite font-bold py-4 rounded-xl hover:opacity-90 transition flex items-center justify-center gap-2 shadow-lg shadow-crimson/20"
                >
                  Generate Slides ({selectedClaims.length} Claims) <ArrowRight size={20} />
                </button>
              </div>
            </motion.div>
          )}

          {stage === 'final' && (
            <motion.div key="final_slides" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
              {/* Changed to text-offwhite */}
              <motion.h2 initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="text-3xl font-bold text-offwhite mb-8 drop-shadow">
                Generated Deck ({slides.length} Slides)
              </motion.h2>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 pb-12">
                <AnimatePresence>
                  {slides.map((slide, index) => (
                    <motion.div 
                      key={index} 
                      layout
                      initial={{ opacity: 0, y: 50 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className="bg-darkgray shadow-2xl rounded-2xl p-8 text-offwhite min-h-[300px] flex flex-col border border-crimson/20 hover:shadow-crimson/20 hover:-translate-y-1 transition-all duration-300"
                    >
                      <h3 className="text-2xl font-bold text-crimson mb-2">{slide.title}</h3>
                      {slide.subtitle && <p className="text-sm text-offwhite/60 mb-4 pb-4 border-b border-crimson/10">{slide.subtitle}</p>}
                      
                      <ul className={`space-y-3 text-offwhite/80 flex-1 mt-2 ${slide.bullets?.length === 1 ? 'flex items-center justify-center' : ''}`}>
                        {slide.bullets?.map((point, i) => (
                          <li key={i} className={`flex items-start gap-3 ${slide.bullets?.length === 1 ? 'text-xl text-center font-medium text-offwhite' : 'text-base'}`}>
                            {slide.bullets?.length > 1 && <span className="text-crimson mt-1.5 text-xs">●</span>}
                            <span>{point}</span>
                          </li>
                        ))}
                      </ul>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

export default App;