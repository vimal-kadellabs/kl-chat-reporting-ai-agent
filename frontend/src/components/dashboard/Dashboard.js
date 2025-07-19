import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const Dashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardStats();
  }, []);

  const fetchDashboardStats = async () => {
    try {
      const [users, properties, auctions, bids] = await Promise.all([
        axios.get('/users'),
        axios.get('/properties'),
        axios.get('/auctions'),
        axios.get('/bids')
      ]);

      setStats({
        totalUsers: users.data.length,
        totalProperties: properties.data.length,
        totalAuctions: auctions.data.length,
        totalBids: bids.data.length,
        liveAuctions: auctions.data.filter(a => a.status === 'live').length,
        upcomingAuctions: auctions.data.filter(a => a.status === 'upcoming').length
      });
    } catch (error) {
      console.error('Error fetching dashboard stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center">
        <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl p-8">
          <div className="loading-dots">
            <div className="loading-dot"></div>
            <div className="loading-dot"></div>
            <div className="loading-dot"></div>
          </div>
          <span className="ml-3 text-slate-600 font-medium">Loading dashboard...</span>
        </div>
      </div>
    );
  }

  const statCards = [
    {
      title: 'Total Properties',
      value: stats.totalProperties,
      icon: '🏠',
      description: 'Available for auction',
      gradient: 'from-blue-500 to-cyan-500',
      bgColor: 'bg-blue-50',
      textColor: 'text-blue-600'
    },
    {
      title: 'Active Auctions',
      value: stats.totalAuctions,
      icon: '🏛️',
      description: 'Live & upcoming',
      gradient: 'from-purple-500 to-indigo-500',
      bgColor: 'bg-purple-50',
      textColor: 'text-purple-600'
    },
    {
      title: 'Total Bids',
      value: stats.totalBids,
      icon: '💰',
      description: 'Placed by investors',
      gradient: 'from-green-500 to-emerald-500',
      bgColor: 'bg-green-50',
      textColor: 'text-green-600'
    },
    {
      title: 'Live Auctions',
      value: stats.liveAuctions,
      icon: '🔴',
      description: 'Currently active',
      gradient: 'from-red-500 to-rose-500',
      bgColor: 'bg-red-50',
      textColor: 'text-red-600'
    },
    {
      title: 'Upcoming',
      value: stats.upcomingAuctions,
      icon: '📅',
      description: 'Scheduled soon',
      gradient: 'from-orange-500 to-amber-500',
      bgColor: 'bg-orange-50',
      textColor: 'text-orange-600'
    },
    {
      title: 'Investors',
      value: stats.totalUsers,
      icon: '👥',
      description: 'Active users',
      gradient: 'from-slate-500 to-gray-500',
      bgColor: 'bg-slate-50',
      textColor: 'text-slate-600'
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-slate-200/60 shadow-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
                <span className="text-white font-bold text-lg">🏠</span>
              </div>
              <div>
                <h1 className="text-xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                  Chat Reporting Agent
                </h1>
                <p className="text-slate-500 text-sm">Real Estate Intelligence Platform</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="hidden sm:block text-right">
                <p className="text-sm font-medium text-slate-600">Welcome back,</p>
                <p className="text-lg font-semibold text-slate-900">{user?.name}</p>
              </div>
              <div className="w-10 h-10 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full flex items-center justify-center shadow-md">
                <span className="text-white font-medium">
                  {user?.name?.charAt(0).toUpperCase()}
                </span>
              </div>
              <button
                onClick={handleLogout}
                className="px-4 py-2 text-sm font-medium text-slate-600 hover:text-slate-900 bg-white rounded-lg border border-slate-200 hover:bg-slate-50 transition-all duration-200 shadow-sm hover:shadow-md"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content - Two Column Layout */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          {/* LEFT SIDE - AI Analysis Section (Top Priority) */}
          <div className="space-y-6">
            <div className="bg-white/60 backdrop-blur-sm rounded-2xl shadow-xl border border-white/20 overflow-hidden">
              <div className="relative">
                {/* Background Pattern */}
                <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/10 via-purple-500/5 to-cyan-500/10"></div>
                <div className="absolute inset-0 opacity-30">
                  <div className="absolute top-0 left-0 w-full h-full bg-[radial-gradient(circle_at_50%_50%,rgba(99,102,241,0.1),transparent_70%)]"></div>
                </div>
                
                <div className="relative p-8">
                  <div className="max-w-lg mx-auto text-center">
                    {/* Clean section without title and icon */}
                    <div className="mb-8">
                      {/* <div className="w-16 h-16 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg animate-pulse">
                        <span className="text-white text-2xl">🤖</span>
                      </div> */}
                      <p className="text-xl text-slate-700 mb-6 leading-relaxed font-medium">
                        Transform your auction data into actionable insights with natural language queries
                      </p>
                    </div>
                    
                    {/* Clean input interface */}
                    <div className="relative group mb-8">
                      <div className="absolute inset-0 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-2xl blur opacity-25 group-hover:opacity-40 transition-opacity duration-300"></div>
                      <button
                        onClick={() => navigate('/chat')}
                        className="relative w-full bg-white/90 backdrop-blur-sm rounded-2xl px-8 py-6 shadow-xl border border-white/30 hover:bg-white transition-all duration-300 transform hover:scale-[1.02] hover:shadow-2xl group"
                      >
                        <div className="flex items-center justify-center space-x-3">
                          <div className="w-10 h-10 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-xl flex items-center justify-center shadow-md group-hover:shadow-lg transition-shadow duration-300">
                            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                            </svg>
                          </div>
                          <div className="text-left">
                            <div className="text-lg font-semibold text-slate-900 group-hover:text-indigo-600 transition-colors duration-300">
                              Start Chat
                            </div>
                            <div className="text-sm text-slate-600">
                              Ask questions in your language
                            </div>
                          </div>
                        </div>
                      </button>
                    </div>
                    
                    {/* Feature highlights - compact version */}
                    <div className="grid grid-cols-3 gap-4">
                      <div className="text-center">
                        <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-xl flex items-center justify-center mx-auto mb-2 shadow-md">
                          <span className="text-white text-sm">📊</span>
                        </div>
                        <p className="text-xs font-medium text-slate-700">Smart Analytics</p>
                      </div>
                      <div className="text-center">
                        <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl flex items-center justify-center mx-auto mb-2 shadow-md">
                          <span className="text-white text-sm">📈</span>
                        </div>
                        <p className="text-xs font-medium text-slate-700">Dynamic Charts</p>
                      </div>
                      <div className="text-center">
                        <div className="w-10 h-10 bg-gradient-to-r from-green-500 to-emerald-500 rounded-xl flex items-center justify-center mx-auto mb-2 shadow-md">
                          <span className="text-white text-sm">🎯</span>
                        </div>
                        <p className="text-xs font-medium text-slate-700">Quick Insights</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Market Activity Card - Enhanced */}
            {/* <div className="bg-white/60 backdrop-blur-sm rounded-2xl shadow-lg border border-white/20 p-6">
              <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center">
                <div className="w-8 h-8 bg-gradient-to-r from-green-500 to-emerald-500 rounded-lg flex items-center justify-center mr-3">
                  <span className="text-white text-sm">📈</span>
                </div>
                Market Activity
              </h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center p-3 rounded-xl bg-green-50 border border-green-100">
                  <span className="text-slate-700 font-medium">Live Auctions</span>
                  <span className="font-bold text-green-600 text-xl">{stats.liveAuctions}</span>
                </div>
                <div className="flex justify-between items-center p-3 rounded-xl bg-blue-50 border border-blue-100">
                  <span className="text-slate-700 font-medium">Upcoming Auctions</span>
                  <span className="font-bold text-blue-600 text-xl">{stats.upcomingAuctions}</span>
                </div>
                <div className="flex justify-between items-center p-3 rounded-xl bg-slate-50 border border-slate-100">
                  <span className="text-slate-700 font-medium">Total Properties</span>
                  <span className="font-bold text-slate-900 text-xl">{stats.totalProperties}</span>
                </div>
              </div>
            </div> */}
          </div>

          {/* RIGHT SIDE - Compact Stats Cards */}
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-4 max-h-[600px] overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-slate-300 scrollbar-track-slate-100">
              {statCards.map((card, index) => (
                <div 
                  key={index} 
                  className="bg-white/60 backdrop-blur-sm rounded-2xl shadow-lg border border-white/20 p-4 transition-all duration-300 hover:scale-105 hover:shadow-xl hover:bg-white/80 group cursor-pointer transform-gpu"
                  style={{ 
                    animationDelay: `${index * 0.1}s`,
                    animation: `fadeInUp 0.6s ease-out forwards`
                  }}
                >
                  <div className="flex items-start justify-between h-full">
                    <div className="flex-1">
                      <p className="text-xs font-medium text-slate-500 mb-1 uppercase tracking-wider">
                        {card.title}
                      </p>
                      <p className="text-2xl font-bold text-slate-900 mb-1 group-hover:text-indigo-600 transition-colors duration-300">
                        {card.value || 0}
                      </p>
                      <p className="text-xs text-slate-400 leading-relaxed">
                        {card.description}
                      </p>
                    </div>
                    <div className={`w-12 h-12 ${card.bgColor} rounded-xl flex items-center justify-center shadow-md group-hover:shadow-lg transition-all duration-300 group-hover:scale-110`}>
                      <span className="text-lg opacity-80 group-hover:opacity-100 transition-opacity duration-300">
                        {card.icon}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Investor Engagement Card - Enhanced */}
            {/* <div className="bg-white/60 backdrop-blur-sm rounded-2xl shadow-lg border border-white/20 p-6">
              <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center">
                <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center mr-3">
                  <span className="text-white text-sm">👥</span>
                </div>
                Investor Engagement
              </h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center p-3 rounded-xl bg-purple-50 border border-purple-100">
                  <span className="text-slate-700 font-medium">Active Investors</span>
                  <span className="font-bold text-purple-600 text-xl">{stats.totalUsers}</span>
                </div>
                <div className="flex justify-between items-center p-3 rounded-xl bg-orange-50 border border-orange-100">
                  <span className="text-slate-700 font-medium">Total Bids</span>
                  <span className="font-bold text-orange-600 text-xl">{stats.totalBids}</span>
                </div>
                <div className="flex justify-between items-center p-3 rounded-xl bg-slate-50 border border-slate-100">
                  <span className="text-slate-700 font-medium">Avg. Bids/Auction</span>
                  <span className="font-bold text-slate-900 text-xl">
                    {stats.totalAuctions > 0 ? Math.round(stats.totalBids / stats.totalAuctions) : 0}
                  </span>
                </div>
              </div>
            </div> */}
          </div>
        </div>
      </main>

      <style jsx>{`
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .scrollbar-thin::-webkit-scrollbar {
          width: 6px;
        }

        .scrollbar-thin::-webkit-scrollbar-track {
          background: #f1f5f9;
          border-radius: 10px;
        }

        .scrollbar-thin::-webkit-scrollbar-thumb {
          background: #cbd5e1;
          border-radius: 10px;
        }

        .scrollbar-thin::-webkit-scrollbar-thumb:hover {
          background: #94a3b8;
        }
      `}</style>
    </div>
  );
};

export default Dashboard;