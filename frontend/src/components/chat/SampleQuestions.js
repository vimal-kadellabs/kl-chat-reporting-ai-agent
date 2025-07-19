import React from 'react';

const SampleQuestions = ({ questions, onQuestionClick, onClose }) => {
  const questionCategories = [
    {
      title: 'Market Analysis',
      icon: '📊',
      color: 'bg-blue-100 text-blue-700',
      questions: questions.slice(0, 3)
    },
    {
      title: 'Investor Insights',
      icon: '👥',
      color: 'bg-purple-100 text-purple-700',
      questions: questions.slice(3, 5)
    },
    {
      title: 'Property Trends',
      icon: '🏠',
      color: 'bg-green-100 text-green-700',
      questions: questions.slice(5, 8)
    }
  ];

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header */}
      <div className="p-4 border-b border-slate-200 bg-gradient-to-r from-slate-50 to-blue-50">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="w-6 h-6 bg-gradient-primary rounded-lg flex items-center justify-center">
              <span className="text-white text-xs">💡</span>
            </div>
            <h3 className="font-semibold text-slate-900">Sample Questions</h3>
          </div>
          {onClose && (
            <button
              onClick={onClose}
              className="md:hidden text-slate-400 hover:text-slate-600 transition-colors p-1"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
        <p className="text-xs text-slate-500 mt-1">Click any question to get started</p>
      </div>
      
      {/* Categories */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {questionCategories.map((category, categoryIndex) => (
          <div key={categoryIndex} className="fade-in" style={{ animationDelay: `${categoryIndex * 0.1}s` }}>
            <div className="flex items-center space-x-2 mb-3">
              <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${category.color}`}>
                <span className="text-sm">{category.icon}</span>
              </div>
              <h4 className="font-medium text-slate-800 text-sm">{category.title}</h4>
            </div>
            
            <div className="space-y-2">
              {category.questions.map((question, index) => (
                <button
                  key={index}
                  onClick={() => onQuestionClick(question)}
                  className="w-full text-left p-3 text-sm bg-slate-50 hover:bg-slate-100 rounded-lg transition-all duration-200 border border-slate-200 hover:border-slate-300 hover:shadow-sm group"
                >
                  <div className="flex items-start justify-between">
                    <span className="text-slate-700 leading-relaxed pr-2 group-hover:text-slate-900 transition-colors">
                      {question}
                    </span>
                    <svg className="w-4 h-4 text-slate-400 group-hover:text-slate-600 transition-colors flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-3.582 8-8 8a8.013 8.013 0 01-7-4c0 0 0 0 0 0 .611.509 1.323.904 2.091 1.169M3 12c0-4.418 3.582-8 8-8s8 3.582 8 8" />
                    </svg>
                  </div>
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
      
      {/* Footer Tips */}
      <div className="p-4 border-t border-slate-200 bg-slate-50">
        <div className="modern-card p-3 bg-gradient-cool border-0">
          <h4 className="font-medium text-slate-800 mb-2 text-sm flex items-center">
            <span className="w-4 h-4 bg-yellow-400 rounded-full flex items-center justify-center mr-2">
              <span className="text-xs">💡</span>
            </span>
            Quick Tips
          </h4>
          <ul className="text-xs text-slate-600 space-y-1.5">
            <li className="flex items-start">
              <span className="text-yellow-500 mr-2 mt-0.5">•</span>
              Ask about specific regions or time periods
            </li>
            <li className="flex items-start">
              <span className="text-yellow-500 mr-2 mt-0.5">•</span>
              Request comparisons between metrics
            </li>
            <li className="flex items-start">
              <span className="text-yellow-500 mr-2 mt-0.5">•</span>
              Inquire about trends and patterns
            </li>
            <li className="flex items-start">
              <span className="text-yellow-500 mr-2 mt-0.5">•</span>
              Ask for top performers or rankings
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default SampleQuestions;