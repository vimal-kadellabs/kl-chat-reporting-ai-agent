import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import ChatMessage from './ChatMessage';
import SampleQuestions from './SampleQuestions';

const ChatInterface = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [sampleQuestions, setSampleQuestions] = useState([]);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    fetchSampleQuestions();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const fetchSampleQuestions = async () => {
    try {
      const response = await axios.get('/sample-questions');
      setSampleQuestions(response.data.questions);
    } catch (error) {
      console.error('Error fetching sample questions:', error);
    }
  };

  const handleSendMessage = async (message = inputMessage) => {
    if (!message.trim()) return;

    const userMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: message,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setLoading(true);
    setSidebarOpen(false); // Close sidebar on mobile after question selection

    try {
      const response = await axios.post('/chat', {
        message: message,
        user_id: user.id
      });

      const botMessage = {
        id: (Date.now() + 1).toString(),
        type: 'bot',
        content: response.data.response,
        chartData: response.data.chart_data,
        chartType: response.data.chart_type,
        summaryPoints: response.data.summary_points,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        id: (Date.now() + 1).toString(),
        type: 'bot',
        content: 'Sorry, I encountered an error while processing your request. Please try again.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="h-screen bg-slate-50 bg-pattern flex flex-col">
      {/* Enhanced Header */}
      <header className="bg-white border-b border-slate-200 shadow-sm flex-shrink-0 relative">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-4">
            {/* Left: Back Button */}
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/dashboard')}
                className="btn-outline p-2 hover:scale-105 transition-all duration-200"
                title="Back to Dashboard"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
            </div>

            {/* Center: Title */}
            <div className="flex-1 text-center">
              <div className="flex items-center justify-center space-x-3">
                {/* <div className="w-8 h-8 bg-gradient-primary rounded-lg flex items-center justify-center">
                  <span className="text-white text-lg">🤖</span>
                </div> */}
                <div>
                  <h1 className="text-xl font-bold text-gradient">
                    Chat Reporting and Analytics Agent
                  </h1>
                  <p className="text-xs text-slate-500">Ask anything about real estate & auctions</p>
                </div>
              </div>
            </div>

            {/* Right: User Menu */}
            <div className="flex items-center space-x-3">
              <div className="hidden sm:block text-right">
                <p className="text-sm font-medium text-slate-700">{user?.name}</p>
              </div>
              <div className="w-8 h-8 bg-slate-200 rounded-full flex items-center justify-center">
                <span className="text-slate-600 text-sm font-medium">
                  {user?.name?.charAt(0).toUpperCase()}
                </span>
              </div>
              <button
                onClick={handleLogout}
                className="text-slate-400 hover:text-slate-600 transition-colors"
                title="Logout"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
              </button>

              {/* Mobile Sidebar Toggle */}
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="md:hidden btn-outline p-2"
                title="Toggle Questions"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Chat Messages Area */}
        <div className="flex-1 flex flex-col">
          <div className="flex-1 overflow-y-auto p-4 space-y-6">
            {messages.length === 0 ? (
              <div className="text-center py-16 fade-in">
                {/* <div className="w-20 h-20 bg-gradient-cool rounded-full flex items-center justify-center mx-auto mb-6">
                  <span className="text-3xl">👋</span>
                </div>
                <h2 className="text-2xl font-bold text-slate-800 mb-3">
                  Welcome to AI Analytics!
                </h2>
                <p className="text-lg text-slate-600 mb-6 max-w-md mx-auto">
                  Ask me anything about real estate auctions, bidding trends, or investor insights.
                </p> */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-2xl mx-auto">
                  <div className="modern-card p-4">
                    <div className="text-2xl mb-2">📊</div>
                    <h3 className="font-semibold text-slate-800 mb-1">Market Analysis</h3>
                    <p className="text-sm text-slate-600">Regional performance and trends</p>
                  </div>
                  <div className="modern-card p-4">
                    <div className="text-2xl mb-2">👥</div>
                    <h3 className="font-semibold text-slate-800 mb-1">Investor Insights</h3>
                    <p className="text-sm text-slate-600">Performance and strategies</p>
                  </div>
                  <div className="modern-card p-4">
                    <div className="text-2xl mb-2">🏠</div>
                    <h3 className="font-semibold text-slate-800 mb-1">Property Data</h3>
                    <p className="text-sm text-slate-600">Auction results and pricing</p>
                  </div>
                  <div className="modern-card p-4">
                    <div className="text-2xl mb-2">📈</div>
                    <h3 className="font-semibold text-slate-800 mb-1">Trend Analysis</h3>
                    <p className="text-sm text-slate-600">Market patterns and forecasts</p>
                  </div>
                </div>
              </div>
            ) : (
              messages.map((message) => (
                <ChatMessage key={message.id} message={message} />
              ))
            )}
            
            {loading && (
              <div className="flex justify-start fade-in">
                <div className="modern-card p-4 max-w-sm">
                  <div className="flex items-center space-x-3">
                    <div className="loading-dots">
                      <div className="loading-dot"></div>
                      <div className="loading-dot"></div>
                      <div className="loading-dot"></div>
                    </div>
                    <span className="text-slate-600 text-sm">AI is analyzing your query...</span>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Enhanced Input Area */}
          <div className="bg-white border-t border-slate-200 shadow-lg flex-shrink-0">
            <div className="max-w-4xl mx-auto p-2">
              <div className="flex space-x-2">
                <div className="flex-1 relative">
                  <textarea
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Ask anything about real estate auctions..."
                    className="input-modern w-full resize-none focus-ring"
                    rows="2"
                    disabled={loading}
                    style={{ padding: '0.5rem 0.75rem' }}
                  />
                  {inputMessage && (
                    <div className="absolute right-2 top-2 text-xs text-slate-400">
                      Press Enter to send
                    </div>
                  )}
                </div>
                <button
                  onClick={() => handleSendMessage()}
                  disabled={loading || !inputMessage.trim()}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white border-none rounded-lg px-3 py-2 font-medium transition-all duration-200 cursor-pointer shadow-sm hover:shadow-md disabled:opacity-60 disabled:cursor-not-allowed flex items-center space-x-1.5"
                >
                  {loading ? (
                    <div className="loading-dots">
                      <div className="loading-dot bg-white"></div>
                      <div className="loading-dot bg-white"></div>
                      <div className="loading-dot bg-white"></div>
                    </div>
                  ) : (
                    <>
                      <span className="text-sm">Send</span>
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                      </svg>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Enhanced Sample Questions Sidebar */}
        <div className={`sidebar-modern w-80 md:block ${sidebarOpen ? 'block' : 'hidden'} md:relative md:translate-x-0`}>
          <SampleQuestions 
            questions={sampleQuestions} 
            onQuestionClick={handleSendMessage}
            onClose={() => setSidebarOpen(false)}
          />
        </div>
      </div>

      {/* Mobile Overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  );
};

export default ChatInterface;