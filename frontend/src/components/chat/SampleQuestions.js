import React from 'react';

const SampleQuestions = ({ questions, onQuestionClick, onClose, loading = false }) => {
  const questionCategories = [
    {
      title: 'Market Analysis',
      color: 'bg-blue-50 border-blue-100',
      iconBg: 'bg-blue-500',
      textColor: 'text-blue-700',
      questions: questions.slice(0, 6)
    },
    {
      title: 'Investor Insights',
      color: 'bg-purple-50 border-purple-100',
      iconBg: 'bg-purple-500',
      textColor: 'text-purple-700',
      questions: questions.slice(6, 12)
    },
    {
      title: 'Property Trends',
      color: 'bg-green-50 border-green-100',
      iconBg: 'bg-green-500',
      textColor: 'text-green-700',
      questions: questions.slice(12, 18)
    },
    {
      title: 'Quick Analytics',
      color: 'bg-orange-50 border-orange-100',
      iconBg: 'bg-orange-500',
      textColor: 'text-orange-700',
      questions: questions.slice(18)
    }
  ];

  const renderCategoryIcon = (categoryIndex) => {
    switch (categoryIndex) {
      case 0:
        return (
          <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
        );
      case 1:
        return (
          <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 515.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
        );
      case 2:
        return (
          <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
          </svg>
        );
      case 3:
        return (
          <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        );
      default:
        return null;
    }
  };

  return (
    <div className="h-full flex flex-col bg-gradient-to-b from-slate-50 to-white">
      {/* Header */}
      <div className="p-4 bg-white/60 backdrop-blur-sm border-b border-slate-200/50 sticky top-0 z-10">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-xl flex items-center justify-center shadow-sm">
              <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <h3 className="font-semibold text-slate-900 text-sm">Suggested Questions</h3>
              <p className="text-xs text-slate-500">Click any question to get started</p>
            </div>
          </div>
          {onClose && (
            <button
              onClick={onClose}
              className="md:hidden text-slate-400 hover:text-slate-600 transition-colors p-2 rounded-lg hover:bg-slate-100"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
      </div>
      
      {/* Categories */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {questionCategories.map((category, categoryIndex) => (
          <div 
            key={categoryIndex} 
            className={`bg-white/60 backdrop-blur-sm rounded-2xl shadow-sm border ${category.color} overflow-hidden`}
          >
            {/* Category Header */}
            <div className="p-4 border-b border-slate-100">
              <div className="flex items-center space-x-3">
                <div className={`w-8 h-8 ${category.iconBg} rounded-xl flex items-center justify-center shadow-sm`}>
                  {renderCategoryIcon(categoryIndex)}
                </div>
                <h4 className={`font-medium text-sm ${category.textColor}`}>
                  {category.title}
                </h4>
                <span className="text-xs text-slate-400 bg-white px-2 py-1 rounded-full">
                  {category.questions.length}
                </span>
              </div>
            </div>

            {/* Questions */}
            <div className="p-2">
              {category.questions.map((question, questionIndex) => (
                <button
                  key={questionIndex}
                  onClick={() => onQuestionClick(question)}
                  className="w-full text-left p-3 rounded-xl hover:bg-white/80 transition-all duration-200 group border border-transparent hover:border-slate-200 hover:shadow-sm"
                >
                  <div className="flex items-start space-x-3">
                    <div className="w-6 h-6 bg-slate-100 rounded-lg flex items-center justify-center mt-0.5 group-hover:bg-slate-200 transition-colors">
                      <svg className="w-3 h-3 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                    <p className="text-sm text-slate-700 group-hover:text-slate-900 leading-relaxed flex-1">
                      {question}
                    </p>
                  </div>
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default SampleQuestions;