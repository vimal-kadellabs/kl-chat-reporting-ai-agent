import React from 'react';

const SampleQuestions = ({ questions, onQuestionClick }) => {
  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b bg-white">
        <h3 className="font-semibold text-gray-900">Sample Questions</h3>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {questions.map((question, index) => (
          <button
            key={index}
            onClick={() => onQuestionClick(question)}
            className="w-full text-left p-3 text-sm bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors border border-gray-200"
          >
            {question}
          </button>
        ))}
      </div>
      
      <div className="p-4 border-t bg-gray-50">
        <h4 className="font-medium text-gray-900 mb-2">Quick Tips:</h4>
        <ul className="text-xs text-gray-600 space-y-1">
          <li>• Ask about specific regions or time periods</li>
          <li>• Request comparisons between different metrics</li>
          <li>• Inquire about trends and patterns</li>
          <li>• Ask for top performers or rankings</li>
        </ul>
      </div>
    </div>
  );
};

export default SampleQuestions;