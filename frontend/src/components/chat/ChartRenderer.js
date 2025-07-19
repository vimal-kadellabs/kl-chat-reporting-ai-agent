import React, { useState, useEffect } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import LoadingProgressBar from './LoadingProgressBar';

// Professional color palette
const COLORS = ['#6366f1', '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#ec4899', '#84cc16'];

const ChartRenderer = ({ data, type, title, description }) => {
  const [isDownloading, setIsDownloading] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [loadingProgress, setLoadingProgress] = useState(0);

  // Enhanced loading effect with progress
  useEffect(() => {
    let progressInterval;
    
    const startLoading = () => {
      setIsLoading(true);
      setLoadingProgress(0);
      
      progressInterval = setInterval(() => {
        setLoadingProgress(prev => {
          if (prev >= 100) {
            clearInterval(progressInterval);
            setTimeout(() => setIsLoading(false), 200);
            return 100;
          }
          return prev + 8;
        });
      }, 120);
    };

    startLoading();

    return () => {
      if (progressInterval) clearInterval(progressInterval);
    };
  }, [data, type]);

  // Reset loading when data changes
  useEffect(() => {
    setIsLoading(true);
    setLoadingProgress(0);
  }, [data, type]);

  // Enhanced error handling
  if (!data) {
    return <div className="text-center py-8 text-gray-500">No chart data provided</div>;
  }
  
  if (!data.data && !Array.isArray(data)) {
    return <div className="text-center py-8 text-gray-500">No data available</div>;
  }
  
  // Support both old format (data.data) and new format (direct array)
  const chartData = Array.isArray(data) ? data : data.data;
  
  if (!Array.isArray(chartData)) {
    return <div className="text-center py-8 text-gray-500">Invalid data format</div>;
  }
  
  if (chartData.length === 0) {
    return <div className="text-center py-8 text-gray-500">No data points available</div>;
  }

  const downloadChart = async () => {
    setIsDownloading(true);
    try {
      // Create a downloadable JSON file
      const jsonData = {
        title: title || 'Chart Data',
        type: type,
        data: chartData,
        generated: new Date().toISOString()
      };
      
      const blob = new Blob([JSON.stringify(jsonData, null, 2)], {
        type: 'application/json'
      });
      
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${(title || 'chart-data').replace(/\s+/g, '-').toLowerCase()}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download failed:', error);
    } finally {
      setIsDownloading(false);
    }
  };

  // Loading component with progress bar
  const LoadingChart = () => (
    <div className="w-full h-96 flex flex-col items-center justify-center p-8">
      <div className="w-full max-w-sm">
        <LoadingProgressBar 
          progress={loadingProgress} 
          text="Loading chart visualization..." 
        />
      </div>
      <div className="mt-4 text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto mb-2"></div>
        <div className="text-slate-600 text-xs">Processing data...</div>
      </div>
    </div>
  );

  const renderChart = () => {
    if (isLoading) {
      return <LoadingChart />;
    }

    switch (type) {
      case 'bar':
        return (
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis 
                dataKey={Object.keys(chartData[0] || {})[0] || 'name'} 
                tick={{ fontSize: 12, fill: '#64748b' }}
                tickLine={{ stroke: '#cbd5e1' }}
              />
              <YAxis 
                tick={{ fontSize: 12, fill: '#64748b' }}
                tickLine={{ stroke: '#cbd5e1' }}
                axisLine={{ stroke: '#cbd5e1' }}
              />
              <Tooltip 
                formatter={(value, name) => [
                  typeof value === 'number' ? value.toLocaleString() : value,
                  name
                ]}
                contentStyle={{
                  backgroundColor: '#ffffff',
                  border: '1px solid #e2e8f0',
                  borderRadius: '8px',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                }}
              />
              <Legend />
              {Object.keys(chartData[0] || {}).slice(1).map((key, index) => (
                <Bar 
                  key={key} 
                  dataKey={key} 
                  fill={COLORS[index % COLORS.length]}
                  name={key.charAt(0).toUpperCase() + key.slice(1).replace(/_/g, ' ')}
                  radius={[2, 2, 0, 0]}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        );

      case 'line':
        return (
          <ResponsiveContainer width="100%" height={320}>
            <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis 
                dataKey={Object.keys(chartData[0] || {})[0] || 'name'} 
                tick={{ fontSize: 12, fill: '#64748b' }}
                tickLine={{ stroke: '#cbd5e1' }}
              />
              <YAxis 
                tick={{ fontSize: 12, fill: '#64748b' }}
                tickLine={{ stroke: '#cbd5e1' }}
                axisLine={{ stroke: '#cbd5e1' }}
              />
              <Tooltip 
                formatter={(value, name) => [
                  typeof value === 'number' ? value.toLocaleString() : value,
                  name
                ]}
                contentStyle={{
                  backgroundColor: '#ffffff',
                  border: '1px solid #e2e8f0',
                  borderRadius: '8px',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                }}
              />
              <Legend />
              {Object.keys(chartData[0] || {}).slice(1).map((key, index) => (
                <Line 
                  key={key} 
                  type="monotone" 
                  dataKey={key} 
                  stroke={COLORS[index % COLORS.length]}
                  strokeWidth={3}
                  dot={{ fill: COLORS[index % COLORS.length], strokeWidth: 2, r: 4 }}
                  name={key.charAt(0).toUpperCase() + key.slice(1).replace(/_/g, ' ')}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        );

      case 'pie':
      case 'donut':
        const pieData = chartData.map((item, index) => ({
          name: item[Object.keys(item || {})[0]] || item.name || 'Unknown',
          value: item[Object.keys(item || {})[1]] || item.value || 0,
          color: COLORS[index % COLORS.length]
        }));

        return (
          <ResponsiveContainer width="100%" height={400}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={type === 'donut' ? 120 : 120}
                innerRadius={type === 'donut' ? 60 : 0}
                fill="#8884d8"
                dataKey="value"
              >
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip 
                formatter={(value) => [value.toLocaleString(), 'Value']}
                contentStyle={{
                  backgroundColor: '#ffffff',
                  border: '1px solid #e2e8f0',
                  borderRadius: '8px',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        );

      case 'none':
        return <div className="text-center py-8 text-gray-500">Chart not available for this analysis</div>;

      default:
        return (
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis 
                dataKey={Object.keys(chartData[0] || {})[0] || 'name'} 
                tick={{ fontSize: 12, fill: '#64748b' }}
              />
              <YAxis tick={{ fontSize: 12, fill: '#64748b' }} />
              <Tooltip 
                formatter={(value, name) => [
                  typeof value === 'number' ? value.toLocaleString() : value,
                  name
                ]}
              />
              <Legend />
              {Object.keys(chartData[0] || {}).slice(1).map((key, index) => (
                <Bar 
                  key={key} 
                  dataKey={key} 
                  fill={COLORS[index % COLORS.length]}
                  name={key.charAt(0).toUpperCase() + key.slice(1).replace(/_/g, ' ')}
                  radius={[2, 2, 0, 0]}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        );
    }
  };

  return (
    <div className="w-full">
      {/* Header with title and download button */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex-1">
          {title && (
            <h4 className="font-semibold text-slate-800 text-base mb-1">{title}</h4>
          )}
          {description && (
            <p className="text-sm text-slate-600">{description}</p>
          )}
        </div>
        {!isLoading && (
          <button
            onClick={downloadChart}
            disabled={isDownloading}
            className="flex items-center space-x-2 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs rounded-lg transition-colors duration-200 disabled:opacity-50"
            title="Download chart data"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <span>{isDownloading ? 'Downloading...' : 'Download'}</span>
          </button>
        )}
      </div>
      
      {/* Chart */}
      {renderChart()}
    </div>
  );
};

export default ChartRenderer;