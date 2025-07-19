import React, { useState, useMemo, useEffect } from 'react';

const TableRenderer = ({ data, title, description }) => {
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });
  const [currentPage, setCurrentPage] = useState(1);
  const [isDownloading, setIsDownloading] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  
  const itemsPerPage = 10;

  // Simulate loading effect
  useEffect(() => {
    const loadingTimer = setTimeout(() => {
      setIsLoading(false);
    }, 1200); // 1.2 second loading effect

    return () => clearTimeout(loadingTimer);
  }, [data]);

  // Reset loading when data changes
  useEffect(() => {
    setIsLoading(true);
  }, [data]);

  if (!data || !data.headers || !data.rows) {
    return (
      <div className="text-center py-8 text-gray-500">
        No table data available
      </div>
    );
  }

  const { headers, rows } = data;

  // Loading component
  const LoadingTable = () => (
    <div className="w-full">
      <div className="animate-pulse space-y-4">
        <div className="h-4 bg-slate-200 rounded w-3/4"></div>
        <div className="border border-slate-200 rounded-lg overflow-hidden">
          <div className="bg-slate-50 p-4 border-b">
            <div className="grid grid-cols-4 gap-4">
              {[1, 2, 3, 4].map(i => (
                <div key={i} className="h-3 bg-slate-200 rounded"></div>
              ))}
            </div>
          </div>
          {[1, 2, 3, 4, 5].map(row => (
            <div key={row} className="p-4 border-b border-slate-100">
              <div className="grid grid-cols-4 gap-4">
                {[1, 2, 3, 4].map(col => (
                  <div key={col} className="h-3 bg-slate-100 rounded"></div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
      <div className="text-center mt-4">
        <div className="inline-flex items-center text-slate-600 text-sm">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-slate-600 mr-2"></div>
          Loading table data...
        </div>
      </div>
    </div>
  );

  // Sorting logic
  const sortedRows = useMemo(() => {
    if (!sortConfig.key) return rows;

    const columnIndex = headers.indexOf(sortConfig.key);
    if (columnIndex === -1) return rows;

    return [...rows].sort((a, b) => {
      const aVal = a[columnIndex];
      const bVal = b[columnIndex];

      // Handle numbers vs strings
      const aNum = parseFloat(String(aVal).replace(/[$,%]/g, ''));
      const bNum = parseFloat(String(bVal).replace(/[$,%]/g, ''));

      let comparison = 0;
      if (!isNaN(aNum) && !isNaN(bNum)) {
        comparison = aNum - bNum;
      } else {
        comparison = String(aVal).localeCompare(String(bVal));
      }

      return sortConfig.direction === 'desc' ? -comparison : comparison;
    });
  }, [rows, headers, sortConfig]);

  // Pagination logic
  const totalPages = Math.ceil(sortedRows.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentRows = sortedRows.slice(startIndex, endIndex);

  const handleSort = (header) => {
    let direction = 'asc';
    if (sortConfig.key === header && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key: header, direction });
    setCurrentPage(1); // Reset to first page when sorting
  };

  const downloadTable = async () => {
    setIsDownloading(true);
    try {
      // Create CSV content
      const csvContent = [
        headers.join(','),
        ...sortedRows.map(row => 
          row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(',')
        )
      ].join('\n');

      // Create blob and download
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${(title || 'table-data').replace(/\s+/g, '-').toLowerCase()}.csv`;
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

  const getSortIcon = (header) => {
    if (sortConfig.key !== header) {
      return (
        <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
        </svg>
      );
    }

    if (sortConfig.direction === 'asc') {
      return (
        <svg className="w-4 h-4 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
        </svg>
      );
    }

    return (
      <svg className="w-4 h-4 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
      </svg>
    );
  };

  if (isLoading) {
    return <LoadingTable />;
  }

  return (
    <div className="w-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex-1">
          {title && (
            <h4 className="font-semibold text-slate-800 text-base mb-1">{title}</h4>
          )}
          {description && (
            <p className="text-sm text-slate-600">{description}</p>
          )}
        </div>
        <button
          onClick={downloadTable}
          disabled={isDownloading}
          className="flex items-center space-x-2 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs rounded-lg transition-colors duration-200 disabled:opacity-50"
          title="Download table as CSV"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <span>{isDownloading ? 'Downloading...' : 'CSV'}</span>
        </button>
      </div>

      {/* Table */}
      <div className="overflow-hidden border border-slate-200 rounded-lg">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50">
              <tr>
                {headers.map((header, index) => (
                  <th
                    key={index}
                    className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider cursor-pointer hover:bg-slate-100 transition-colors duration-150"
                    onClick={() => handleSort(header)}
                  >
                    <div className="flex items-center space-x-1">
                      <span>{header}</span>
                      {getSortIcon(header)}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-slate-200">
              {currentRows.map((row, rowIndex) => (
                <tr key={rowIndex} className="hover:bg-slate-50 transition-colors duration-150">
                  {row.map((cell, cellIndex) => (
                    <td key={cellIndex} className="px-6 py-4 whitespace-nowrap text-sm text-slate-900">
                      {typeof cell === 'number' ? cell.toLocaleString() : String(cell)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="bg-white px-4 py-3 border-t border-slate-200 sm:px-6">
            <div className="flex items-center justify-between">
              <div className="text-sm text-slate-700">
                Showing <span className="font-medium">{startIndex + 1}</span> to{' '}
                <span className="font-medium">{Math.min(endIndex, sortedRows.length)}</span> of{' '}
                <span className="font-medium">{sortedRows.length}</span> results
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                  disabled={currentPage === 1}
                  className="px-3 py-1 bg-white border border-slate-300 rounded-md text-sm text-slate-700 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-150"
                >
                  Previous
                </button>
                <span className="text-sm text-slate-600">
                  Page {currentPage} of {totalPages}
                </span>
                <button
                  onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                  disabled={currentPage === totalPages}
                  className="px-3 py-1 bg-white border border-slate-300 rounded-md text-sm text-slate-700 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-150"
                >
                  Next
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TableRenderer;