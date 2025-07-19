import React from 'react';
import ChartRenderer from './ChartRenderer';
import TableRenderer from './TableRenderer';
import TypingAnimation from './TypingAnimation';

const ChatMessage = ({ message }) => {
  const isUser = message.type === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} fade-in`}>
      <div className={`max-w-4xl w-full ${isUser ? 'text-right' : 'text-left'}`}>
        {/* User Message Bubble */}
        {isUser && (
          <div className="flex items-start space-x-3 mb-3">
            <div className="flex-1 flex justify-end">
              <div className="chat-bubble-user">
                <p className="leading-relaxed">{message.content}</p>
              </div>
            </div>
            <div className="w-8 h-8 bg-slate-200 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
              <span className="text-slate-600 text-sm font-medium">U</span>
            </div>
          </div>
        )}

        {/* Bot Messages */}
        {!isUser && (
          <div className="flex items-start space-x-3 mb-3">
            <div className="w-8 h-8 bg-gradient-primary rounded-full flex items-center justify-center flex-shrink-0 mt-1">
              <span className="text-white text-sm">🤖</span>
            </div>
            <div className="flex-1 min-w-0">
              
              {/* Summary Points with Typing Animation */}
              {message.summaryPoints && message.summaryPoints.length > 0 && (
                <div className="mb-4">
                  <div className="modern-card bg-blue-50 border-blue-200 p-4">
                    <div className="flex items-center mb-3">
                      <div className="w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center mr-2">
                        <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" clipRule="evenodd" />
                        </svg>
                      </div>
                      <h4 className="font-semibold text-blue-900 text-sm">Key Insights</h4>
                    </div>
                    <div className="space-y-2">
                      {message.summaryPoints.map((point, index) => (
                        <div key={index} className="text-sm text-blue-800 flex items-start">
                          <div className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                          <div className="leading-relaxed flex-1">
                            <TypingAnimation 
                              text={point} 
                              speed={20}
                              startDelay={index * 1000 + 1000} // Stagger each point
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Multiple Charts */}
              {message.charts && message.charts.length > 0 && (
                <div className="mb-6">
                  {/* Charts Grid - Two Column Layout */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {message.charts.map((chart, index) => (
                      <div key={index} className="bg-white/60 backdrop-blur-sm rounded-2xl shadow-sm border border-white/20 overflow-hidden">
                        <div className="bg-gradient-to-r from-slate-50 to-blue-50 px-4 py-3 border-b border-slate-200">
                          <div className="flex items-center">
                            <div className="w-8 h-8 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-xl flex items-center justify-center mr-3 shadow-sm">
                              <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                              </svg>
                            </div>
                            <div className="flex-1">
                              <h4 className="font-semibold text-slate-700 text-sm">
                                Chart {index + 1} of {message.charts.length}
                              </h4>
                              <span className="text-xs text-slate-500 bg-white px-2 py-1 rounded-full ml-2">
                                {chart.type.toUpperCase()}
                              </span>
                            </div>
                          </div>
                        </div>
                        <div className="p-4">
                          <ChartRenderer
                            data={chart.data}
                            type={chart.type}
                            title={chart.title}
                            description={chart.description}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Tables - Full Width */}
              {message.tables && message.tables.length > 0 && (
                <div className="mb-6">
                  {message.tables.map((table, index) => (
                    <div key={index} className="bg-white/60 backdrop-blur-sm rounded-2xl shadow-sm border border-white/20 overflow-hidden mb-4">
                      <div className="bg-gradient-to-r from-slate-50 to-green-50 px-4 py-3 border-b border-slate-200">
                        <div className="flex items-center">
                          <div className="w-8 h-8 bg-gradient-to-r from-green-500 to-emerald-500 rounded-xl flex items-center justify-center mr-3 shadow-sm">
                            <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2H9z" />
                            </svg>
                          </div>
                          <div className="flex-1">
                            <h4 className="font-semibold text-slate-700 text-sm">
                              Data Table {message.tables.length > 1 && `${index + 1} of ${message.tables.length}`}
                            </h4>
                            <span className="text-xs text-slate-500 bg-white px-2 py-1 rounded-full ml-2">
                              INTERACTIVE
                            </span>
                          </div>
                        </div>
                      </div>
                      <div className="p-4">
                        <TableRenderer
                          data={table}
                          title={table.title}
                          description={table.description}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Backward compatibility for single chart */}
              {!message.charts && message.chartData && message.chartType && (
                <div className="mb-4">
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

              {/* Main Response with Typing Animation */}
              {message.content && (
                <div className="modern-card p-6 bg-gradient-to-br from-white to-slate-50 border border-slate-200">
                  <TypingAnimation 
                    text={message.content} 
                    speed={25}
                    startDelay={500}
                  />
                </div>
              )}

            </div>
          </div>
        )}

        {/* Timestamp */}
        <div className={`text-xs text-slate-400 mt-1 ${isUser ? 'text-right mr-11' : 'text-left ml-11'
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