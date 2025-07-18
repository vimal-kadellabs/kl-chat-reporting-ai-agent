import React from 'react';
import ChartRenderer from './ChartRenderer';

const ChatMessage = ({ message }) => {
  const isUser = message.type === 'user';
  
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-4xl w-full ${isUser ? 'text-right' : 'text-left'}`}>
        {/* Message bubble */}
        <div className={`inline-block px-4 py-2 rounded-lg ${
          isUser 
            ? 'bg-indigo-600 text-white' 
            : 'bg-gray-100 text-gray-800'
        }`}>
          {message.content}
        </div>
        
        {/* Summary points for bot messages */}
        {!isUser && message.summaryPoints && message.summaryPoints.length > 0 && (
          <div className="mt-3 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="font-semibold text-blue-900 mb-2">Key Insights:</h4>
            <ul className="space-y-1">
              {message.summaryPoints.map((point, index) => (
                <li key={index} className="text-sm text-blue-800 flex items-start">
                  <span className="text-blue-600 mr-2">•</span>
                  {point}
                </li>
              ))}
            </ul>
          </div>
        )}
        
        {/* Chart for bot messages */}
        {!isUser && message.chartData && message.chartType && (
          <div className="mt-4 bg-white border border-gray-200 rounded-lg p-4">
            <ChartRenderer 
              data={message.chartData} 
              type={message.chartType}
            />
          </div>
        )}
        
        {/* Timestamp */}
        <div className={`text-xs text-gray-500 mt-1 ${
          isUser ? 'text-right' : 'text-left'
        }`}>
          {message.timestamp.toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
};

export default ChatMessage;