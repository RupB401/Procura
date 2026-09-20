import React, { useEffect, useState } from 'react';
import { api } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';
import type { RFQListItem, RFQStatus } from '../lib/types';
import { Plus, FileText, Clock, CheckCircle, XCircle, ChevronRight, Loader2, Search, Filter } from 'lucide-react';

const STATUS_STYLES: Record<RFQStatus, string> = {
  DRAFT: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
  OPEN: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300',
  UNDER_REVIEW: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300',
  AWARDED: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
  CANCELLED: 'bg-red-100 text-red-600 dark:bg-red-900/40 dark:text-red-400',
};

const STATUS_ICONS: Record<RFQStatus, React.ReactNode> = {
  DRAFT: <FileText className="w-3.5 h-3.5" />,
  OPEN: <CheckCircle className="w-3.5 h-3.5" />,
  UNDER_REVIEW: <Clock className="w-3.5 h-3.5" />,
  AWARDED: <CheckCircle className="w-3.5 h-3.5" />,
  CANCELLED: <XCircle className="w-3.5 h-3.5" />,
};

interface RFQListPageProps {
  onSelectRFQ: (id: string) => void;
  onCreateRFQ: () => void;
}

export function RFQListPage({ onSelectRFQ, onCreateRFQ }: RFQListPageProps) {
  const { user } = useAuth();
  const [rfqs, setRfqs] = useState<RFQListItem[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<RFQStatus | 'ALL'>('ALL');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const filteredRfqs = rfqs.filter(rfq => {
    const matchesSearch = rfq.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          (rfq.delivery_location && rfq.delivery_location.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesStatus = statusFilter === 'ALL' || rfq.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  useEffect(() => {
    api.get<RFQListItem[]>('/rfqs')
      .then(setRfqs)
      .catch((e) => setError(e.message))
      .finally(() => setIsLoading(false));
  }, []);

  const formatDeadline = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  const isExpired = (iso: string) => new Date(iso) < new Date();

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            {user?.role === 'BUYER' ? 'My RFQs' : 'Available RFQs'}
          </h2>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {user?.role === 'BUYER'
              ? 'Manage your Request for Quotations'
              : 'Discover and bid on open procurement requests'}
          </p>
        </div>
        {user?.role === 'BUYER' && (
          <button
            id="create-rfq-btn"
            onClick={onCreateRFQ}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-sm font-semibold hover:from-blue-700 hover:to-indigo-700 transition-all shadow-sm"
          >
            <Plus className="w-4 h-4" />
            New RFQ
          </button>
        )}
      </div>

      {/* Search and Filter Bar */}
      <div className="flex flex-col sm:flex-row gap-3 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input 
            type="text" 
            placeholder="Search by title or delivery location..." 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white/50 dark:bg-gray-800/50 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
          />
        </div>
        <div className="relative w-full sm:w-48 shrink-0">
          <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <select 
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as RFQStatus | 'ALL')}
            className="w-full pl-10 pr-4 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white/50 dark:bg-gray-800/50 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm appearance-none"
          >
            <option value="ALL">All Statuses</option>
            {user?.role === 'BUYER' && <option value="DRAFT">Draft</option>}
            <option value="OPEN">Open</option>
            <option value="UNDER_REVIEW">Under Review</option>
            <option value="AWARDED">Awarded</option>
            {user?.role === 'BUYER' && <option value="CANCELLED">Cancelled</option>}
          </select>
        </div>
      </div>

      {isLoading && (
        <div className="flex justify-center py-16">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        </div>
      )}

      {error && (
        <div className="p-4 rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 text-sm">
          {error}
        </div>
      )}

      {!isLoading && !error && rfqs.length === 0 && (
        <div className="text-center py-16 glass-card">
          <FileText className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
          <p className="text-gray-500 dark:text-gray-400 font-medium">No RFQs found</p>
          {user?.role === 'BUYER' && (
            <button
              onClick={onCreateRFQ}
              className="mt-4 text-sm text-blue-600 hover:underline"
            >
              Create your first RFQ →
            </button>
          )}
        </div>
      )}

      <div className="space-y-3">
        {filteredRfqs.map((rfq) => (
          <button
            key={rfq.id}
            id={`rfq-item-${rfq.id}`}
            onClick={() => onSelectRFQ(rfq.id)}
            className="w-full text-left glass-card p-5 hover:shadow-md transition-all group"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_STYLES[rfq.status]}`}>
                    {STATUS_ICONS[rfq.status]}
                    {rfq.status.replace('_', ' ')}
                  </span>
                  <span className="text-xs text-gray-400 dark:text-gray-500 font-mono">
                    {rfq.currency_code}
                  </span>
                </div>
                <h3 className="font-semibold text-gray-900 dark:text-white truncate">{rfq.title}</h3>
                <p className={`text-xs mt-1 ${isExpired(rfq.submission_deadline) && rfq.status === 'OPEN' ? 'text-red-500' : 'text-gray-400 dark:text-gray-500'}`}>
                  Deadline: {formatDeadline(rfq.submission_deadline)}
                  {isExpired(rfq.submission_deadline) && rfq.status === 'OPEN' && ' · Expired'}
                  {rfq.delivery_location && ` · Location: ${rfq.delivery_location}`}
                </p>
              </div>
              <ChevronRight className="w-5 h-5 text-gray-300 dark:text-gray-600 group-hover:text-blue-500 transition-colors shrink-0 mt-1" />
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
