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
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="modern-card p-8">
          <div className="loading-dots">
            <div className="loading-dot"></div>
            <div className="loading-dot"></div>
            <div className="loading-dot"></div>
          </div>
          <span className="ml-3 text-slate-600">Loading dashboard...</span>
        </div>
      </div>
    );
  }

  const statCards = [
    {
      title: 'Total Properties',
      value: stats.totalProperties,
      icon: '🏠',
      gradient: 'gradient-card',
      description: 'Available for auction'
    },
    {
      title: 'Active Auctions',
      value: stats.totalAuctions,
      icon: '🏛️',
      gradient: 'gradient-card-secondary',
      description: 'Live & upcoming'
    },
    {
      title: 'Total Bids',
      value: stats.totalBids,
      icon: '💰',
      gradient: 'gradient-card-accent',
      description: 'Placed by investors'
    },
    {
      title: 'Live Auctions',
      value: stats.liveAuctions,
      icon: '🔴',
      gradient: 'gradient-card-cool',
      description: 'Currently active'
    },
    {
      title: 'Upcoming Auctions',
      value: stats.upcomingAuctions,
      icon: '📅',
      gradient: 'modern-card',
      description: 'Scheduled soon'
    },
    {
      title: 'Active Investors',
      value: stats.totalUsers,
      icon: '👥',
      gradient: 'modern-card',
      description: 'Registered users'
    }
  ];

  return (
    <div className="min-h-screen bg-slate-50 bg-pattern">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center space-x-4">
              <div className="w-10 h-10 bg-gradient-primary rounded-xl flex items-center justify-center">
                <span className="text-white font-bold text-lg">🏠</span>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gradient">
                  Auction Analytics
                </h1>
                <p className="text-slate-500 text-sm">Real Estate Intelligence Platform</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="hidden sm:block text-right">
                <p className="text-sm font-medium text-slate-700">Welcome back,</p>
                <p className="text-lg font-semibold text-slate-900">{user?.name}</p>
              </div>
              <div className="w-10 h-10 bg-slate-200 rounded-full flex items-center justify-center">
                <span className="text-slate-600 font-medium">
                  {user?.name?.charAt(0).toUpperCase()}
                </span>
              </div>
              <button
                onClick={handleLogout}
                className="btn-outline text-sm"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          {statCards.map((card, index) => (
            <div 
              key={index} 
              className={`${card.gradient} p-6 transition-all duration-300 hover:scale-105 fade-in`}
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <p className={`text-sm font-medium ${card.gradient === 'modern-card' ? 'text-slate-500' : 'text-white/80'} mb-1`}>
                    {card.title}
                  </p>
                  <p className={`text-3xl font-bold ${card.gradient === 'modern-card' ? 'text-slate-900' : 'text-white'} mb-1`}>
                    {card.value}
                  </p>
                  <p className={`text-xs ${card.gradient === 'modern-card' ? 'text-slate-400' : 'text-white/60'}`}>
                    {card.description}
                  </p>
                </div>
                <div className="text-3xl opacity-80">
                  {card.icon}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Main CTA Section */}
        <div className="modern-card overflow-hidden slide-up">
          <div className="relative">
            <div className="absolute inset-0 bg-gradient-primary opacity-5"></div>
            <div className="relative p-12 text-center">
              <div className="max-w-3xl mx-auto">
                <div className="w-16 h-16 bg-gradient-primary rounded-2xl flex items-center justify-center mx-auto mb-6">
                  <span className="text-white text-2xl">🤖</span>
                </div>
                <h2 className="text-4xl font-bold text-slate-900 mb-4">
                  AI-Powered Real Estate Analytics
                </h2>
                <p className="text-xl text-slate-600 mb-8 leading-relaxed">
                  Transform your auction data into actionable insights with natural language queries. 
                  Get instant analytics, dynamic charts, and professional recommendations.
                </p>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                  <div className="p-4">
                    <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                      <span className="text-blue-600 text-xl">📊</span>
                    </div>
                    <h3 className="font-semibold text-slate-900 mb-2">Smart Analytics</h3>
                    <p className="text-slate-600 text-sm">Ask complex questions in plain English and get professional insights</p>
                  </div>
                  <div className="p-4">
                    <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                      <span className="text-purple-600 text-xl">📈</span>
                    </div>
                    <h3 className="font-semibold text-slate-900 mb-2">Dynamic Charts</h3>
                    <p className="text-slate-600 text-sm">Interactive visualizations automatically generated for your queries</p>
                  </div>
                  <div className="p-4">
                    <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                      <span className="text-green-600 text-xl">🎯</span>
                    </div>
                    <h3 className="font-semibold text-slate-900 mb-2">Actionable Insights</h3>
                    <p className="text-slate-600 text-sm">Get recommendations and market opportunities tailored to your needs</p>
                  </div>
                </div>

                <button
                  onClick={() => navigate('/chat')}
                  className="btn-modern text-lg px-8 py-4 shadow-lg hover:shadow-xl"
                >
                  <span className="flex items-center">
                    Start AI Analysis
                    <svg className="w-5 h-5 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                    </svg>
                  </span>
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Stats Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-8">
          <div className="modern-card p-6">
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Market Activity</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-slate-600">Live Auctions</span>
                <span className="font-semibold text-green-600">{stats.liveAuctions}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-600">Upcoming Auctions</span>
                <span className="font-semibold text-blue-600">{stats.upcomingAuctions}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-600">Total Properties</span>
                <span className="font-semibold text-slate-900">{stats.totalProperties}</span>
              </div>
            </div>
          </div>

          <div className="modern-card p-6">
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Investor Engagement</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-slate-600">Active Investors</span>
                <span className="font-semibold text-purple-600">{stats.totalUsers}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-600">Total Bids Placed</span>
                <span className="font-semibold text-orange-600">{stats.totalBids}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-600">Avg. Bids/Auction</span>
                <span className="font-semibold text-slate-900">
                  {stats.totalAuctions > 0 ? Math.round(stats.totalBids / stats.totalAuctions) : 0}
                </span>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;