import React, { useState, useEffect } from 'react';
import TypingAnimation from './TypingAnimation';

const CoordinatedTyping = ({ summaryPoints, speed = 25, initialDelay = 1000 }) => {
  const [activeIndex, setActiveIndex] = useState(-1);
  const [completedPoints, setCompletedPoints] = useState(new Set());

  useEffect(() => {
    if (!summaryPoints || summaryPoints.length === 0) return;

    // Start the first point after initial delay
    const startTimer = setTimeout(() => {
      setActiveIndex(0);
    }, initialDelay);

    return () => clearTimeout(startTimer);
  }, [summaryPoints, initialDelay]);

  const handlePointComplete = (index) => {
    setCompletedPoints(prev => new Set([...prev, index]));
    
    // Start next point after a brief pause
    if (index < summaryPoints.length - 1) {
      setTimeout(() => {
        setActiveIndex(index + 1);
      }, 300); // Brief pause between points
    }
  };

  if (!summaryPoints || summaryPoints.length === 0) return null;

  return (
    <div className="space-y-2">
      {summaryPoints.map((point, index) => (
        <div key={index} className="text-sm text-blue-800 flex items-start">
          <div className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-2 mr-3 flex-shrink-0"></div>
          <div className="leading-relaxed flex-1">
            {index < activeIndex ? (
              // Already completed points - show immediately
              <div className="prose prose-sm max-w-none text-blue-800">
                {point}
              </div>
            ) : index === activeIndex ? (
              // Currently typing point - show with animation and cursor
              <TypingAnimation 
                text={point} 
                speed={speed}
                startDelay={0}
                showCursor={true}
                onComplete={() => handlePointComplete(index)}
              />
            ) : (
              // Future points - show placeholder or nothing
              <div className="h-5 opacity-0"></div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};

export default CoordinatedTyping;