import React from 'react';
import ChartRenderer from './ChartRenderer';

const ChatMessage = ({ message }) => {
  const isUser = message.type === 'user';
  
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} fade-in`}>
      <div className={`max-w-4xl w-full ${isUser ? 'text-right' : 'text-left'}`}>
        {/* Message Bubble */}
        <div className="flex items-start space-x-3 mb-3">
          {!isUser && (
            <div className="w-8 h-8 bg-gradient-primary rounded-full flex items-center justify-center flex-shrink-0 mt-1">
              <span className="text-white text-sm">🤖</span>
            </div>
          )}
          <div className={`flex-1 ${isUser ? 'flex justify-end' : ''}`}>
            <div className={isUser ? 'chat-bubble-user' : 'chat-bubble-bot'}>
              <p className="leading-relaxed">{message.content}</p>
            </div>
          </div>
          {isUser && (
            <div className="w-8 h-8 bg-slate-200 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
              <span className="text-slate-600 text-sm font-medium">
                U
              </span>
            </div>
          )}
        </div>
        
        {/* Summary Points for Bot Messages */}
        {!isUser && message.summaryPoints && message.summaryPoints.length > 0 && (
          <div className="ml-11 mb-4">
            <div className="modern-card bg-blue-50 border-blue-200 p-4">
              <div className="flex items-center mb-3">
                <div className="w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center mr-2">
                  <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" clipRule="evenodd" />
                  </svg>
                </div>
                <h4 className="font-semibold text-blue-900 text-sm">Key Insights</h4>
              </div>
              <ul className="space-y-2">
                {message.summaryPoints.map((point, index) => (
                  <li key={index} className="text-sm text-blue-800 flex items-start">
                    <div className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                    <span className="leading-relaxed">{point}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
        
        {/* Chart for Bot Messages */}
        {!isUser && message.chartData && message.chartType && (
          <div className="ml-11 mb-4">
            <div className="modern-card overflow-hidden">
              <div className="bg-gradient-to-r from-slate-50 to-blue-50 px-4 py-3 border-b border-slate-200">
                <div className="flex items-center">
                  <div className="w-5 h-5 bg-slate-400 rounded-full flex items-center justify-center mr-2">
                    <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M2 10a8 8 0 018-8v8h8a8 8 0 11-16 0z" />
                      <path d="M12 2.252A8.014 8.014 0 0117.748 8H12V2.252z" />
                    </svg>
                  </div>
                  <h4 className="font-semibold text-slate-700 text-sm">Data Visualization</h4>
                  <span className="ml-2 text-xs text-slate-500 bg-white px-2 py-1 rounded-full">
                    {message.chartType.toUpperCase()}
                  </span>
                </div>
              </div>
              <div className="p-4">
                <ChartRenderer 
                  data={message.chartData} 
                  type={message.chartType}
                />
              </div>
            </div>
          </div>
        )}
        
        {/* Timestamp */}
        <div className={`text-xs text-slate-400 mt-1 ${
          isUser ? 'text-right mr-11' : 'text-left ml-11'
        }`}>
          {message.timestamp.toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
          })}
        </div>
      </div>
    </div>
  );
};

export default ChatMessage;