import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';

const TypingAnimation = ({ text, speed = 30, startDelay = 0 }) => {
  const [displayedText, setDisplayedText] = useState('');
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isComplete, setIsComplete] = useState(false);
  const [hasStarted, setHasStarted] = useState(false);

  useEffect(() => {
    if (!text) return;

    // Start delay
    const startTimer = setTimeout(() => {
      setHasStarted(true);
    }, startDelay);

    return () => clearTimeout(startTimer);
  }, [text, startDelay]);

  useEffect(() => {
    if (!hasStarted || !text || isComplete) return;

    if (currentIndex < text.length) {
      const timer = setTimeout(() => {
        setDisplayedText(text.slice(0, currentIndex + 1));
        setCurrentIndex(currentIndex + 1);
      }, speed);

      return () => clearTimeout(timer);
    } else {
      setIsComplete(true);
    }
  }, [text, currentIndex, speed, hasStarted, isComplete]);

  // Reset when text changes
  useEffect(() => {
    setDisplayedText('');
    setCurrentIndex(0);
    setIsComplete(false);
    setHasStarted(false);
  }, [text]);

  return (
    <div className="typing-animation">
      <ReactMarkdown 
        className="prose prose-sm max-w-none prose-headings:text-slate-800 prose-headings:font-semibold prose-p:text-slate-700 prose-p:leading-relaxed prose-strong:text-slate-900 prose-ul:text-slate-700 prose-li:text-slate-700"
        components={{
          h2: ({ children }) => (
            <h2 className="text-xl font-semibold text-slate-800 mb-3 flex items-center">
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 className="text-lg font-medium text-slate-800 mb-2 flex items-center">
              {children}
            </h3>
          ),
          p: ({ children }) => (
            <p className="text-slate-700 leading-relaxed mb-3">
              {children}
            </p>
          ),
          strong: ({ children }) => (
            <strong className="font-semibold text-slate-900">
              {children}
            </strong>
          ),
          ul: ({ children }) => (
            <ul className="list-disc list-inside space-y-1 text-slate-700 mb-3">
              {children}
            </ul>
          ),
          li: ({ children }) => (
            <li className="text-slate-700">
              {children}
            </li>
          ),
        }}
      >
        {displayedText}
      </ReactMarkdown>
      
      {/* Typing cursor */}
      {!isComplete && hasStarted && (
        <span className="inline-block w-2 h-5 bg-indigo-600 ml-1 animate-pulse typing-cursor" />
      )}
      
      <style jsx>{`
        .typing-cursor {
          animation: blink 1s infinite;
        }
        
        @keyframes blink {
          0%, 50% { opacity: 1; }
          51%, 100% { opacity: 0; }
        }
      `}</style>
    </div>
  );
};

export default TypingAnimation;