import { useCallback, useEffect, useState } from 'react';
import { api } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';
import type { Clarification, Quote, RFQ } from '../lib/types';
import {
  ArrowLeft, CheckCircle, ChevronDown, ChevronUp, Loader2,
  MessageSquare, Send, ShieldAlert, Trophy, XCircle, Package
} from 'lucide-react';

interface RFQDetailPageProps {
  rfqId: string;
  onBack: () => void;
}

const statusColors: Record<string, string> = {
  DRAFT: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
  OPEN: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300',
  UNDER_REVIEW: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300',
  AWARDED: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
  CANCELLED: 'bg-red-100 text-red-600 dark:bg-red-900/40 dark:text-red-400',
};

export function RFQDetailPage({ rfqId, onBack }: RFQDetailPageProps) {
  const { user } = useAuth();
  const [rfq, setRfq] = useState<RFQ | null>(null);
  const [quotes, setQuotes] = useState<Quote[]>([]);
  const [clarifications, setClarifications] = useState<Clarification[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Quote submission state (vendor)
  const [showQuoteForm, setShowQuoteForm] = useState(false);
  const [quoteInputs, setQuoteInputs] = useState<Record<string, { unit_price: string; lead_time_days: string; notes: string }>>({});

  // Clarification state
  const [clarQuestion, setClarQuestion] = useState('');
  const [answerInputs, setAnswerInputs] = useState<Record<string, string>>({});
  const [expandedQuote, setExpandedQuote] = useState<string | null>(null);

  const loadAll = useCallback(async () => {
    try {
      const rfqData = await api.get<RFQ>(`/rfqs/${rfqId}`);
      setRfq(rfqData);

      // Initialize quote inputs keyed by rfq_item id
      const inputs: typeof quoteInputs = {};
      for (const item of rfqData.items) {
        inputs[item.id] = { unit_price: '', lead_time_days: '', notes: '' };
      }
      setQuoteInputs(inputs);

      // Only load quotes for allowed states
      if (['UNDER_REVIEW', 'AWARDED'].includes(rfqData.status) && user?.role === 'BUYER') {
        const q = await api.get<Quote[]>(`/rfqs/${rfqId}/quotes`);
        setQuotes(q);
      } else if (user?.role === 'VENDOR' && ['OPEN', 'UNDER_REVIEW', 'AWARDED'].includes(rfqData.status)) {
        const q = await api.get<Quote[]>(`/rfqs/${rfqId}/quotes`).catch(() => []);
        setQuotes(q);
      }

      const clars = await api.get<Clarification[]>(`/rfqs/${rfqId}/clarifications`).catch(() => []);
      setClarifications(clars);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load RFQ');
    } finally {
      setIsLoading(false);
    }
  }, [rfqId, user?.role]);

  useEffect(() => { loadAll(); }, [loadAll]);

  const doAction = async (action: string, successMsg?: string) => {
    setActionLoading(action);
    setError(null);
    try {
      const updated = await api.post<RFQ>(`/rfqs/${rfqId}/${action}`);
      setRfq(updated);
      if (successMsg) console.log(successMsg);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Action failed');
    } finally {
      setActionLoading(null);
    }
  };

  const submitQuote = async () => {
    if (!rfq) return;
    setActionLoading('quote');
    setError(null);
    try {
      const items = rfq.items.map((item) => ({
        rfq_item_id: item.id,
        unit_price: parseFloat(quoteInputs[item.id]?.unit_price ?? '0'),
        lead_time_days: parseInt(quoteInputs[item.id]?.lead_time_days ?? '1', 10),
        notes: quoteInputs[item.id]?.notes || undefined,
      }));
      await api.post(`/rfqs/${rfqId}/quotes`, { items });
      setShowQuoteForm(false);
      await loadAll();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to submit quote');
    } finally {
      setActionLoading(null);
    }
  };

  const awardQuote = async (quoteId: string) => {
    setActionLoading(`award-${quoteId}`);
    setError(null);
    try {
      const result = await api.post<{ message: string; erp_payload: unknown }>(`/rfqs/${rfqId}/quotes/${quoteId}/award`);
      console.log('ERP Payload:', JSON.stringify(result.erp_payload, null, 2));
      await loadAll();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to award quote');
    } finally {
      setActionLoading(null);
    }
  };

  const askClarification = async () => {
    if (!clarQuestion.trim()) return;
    setActionLoading('clar');
    try {
      await api.post(`/rfqs/${rfqId}/clarifications`, { question: clarQuestion });
      setClarQuestion('');
      await loadAll();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to ask question');
    } finally {
      setActionLoading(null);
    }
  };

  const answerClarification = async (threadId: string) => {
    const ans = answerInputs[threadId];
    if (!ans?.trim()) return;
    setActionLoading(`ans-${threadId}`);
    try {
      await api.post(`/rfqs/${rfqId}/clarifications/${threadId}/answer`, { answer: ans });
      setAnswerInputs((prev) => ({ ...prev, [threadId]: '' }));
      await loadAll();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to answer');
    } finally {
      setActionLoading(null);
    }
  };

  if (isLoading) return <div className="flex justify-center py-16"><Loader2 className="w-8 h-8 animate-spin text-blue-600" /></div>;
  if (!rfq) return <div className="p-6 text-red-500">{error ?? 'RFQ not found'}</div>;

  const isBuyer = user?.role === 'BUYER';
  const isVendor = user?.role === 'VENDOR';
  const canSubmitQuote = isVendor && rfq.status === 'OPEN' && quotes.length === 0;
  const hasSubmittedQuote = isVendor && quotes.length > 0;

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <button onClick={onBack} className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-blue-600 mb-4">
          <ArrowLeft className="w-4 h-4" /> Back to list
        </button>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${statusColors[rfq.status]}`}>
                {rfq.status.replace('_', ' ')}
              </span>
              <span className="text-xs text-gray-400 font-mono">{rfq.currency_code}</span>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">{rfq.title}</h2>
            {rfq.description && <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">{rfq.description}</p>}
            <p className="text-xs text-gray-400 mt-1">
              Deadline: {new Date(rfq.submission_deadline).toLocaleString()}
            </p>
          </div>

          {/* Buyer actions */}
          {isBuyer && (
            <div className="flex flex-wrap gap-2">
              {rfq.status === 'DRAFT' && (
                <button id="publish-btn" onClick={() => doAction('publish')} disabled={!!actionLoading}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-green-600 text-white text-sm font-semibold hover:bg-green-700 transition-colors disabled:opacity-60">
                  {actionLoading === 'publish' && <Loader2 className="w-4 h-4 animate-spin" />}
                  <CheckCircle className="w-4 h-4" /> Publish
                </button>
              )}
              {rfq.status === 'OPEN' && (
                <button id="close-btn" onClick={() => doAction('close')} disabled={!!actionLoading}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-yellow-600 text-white text-sm font-semibold hover:bg-yellow-700 transition-colors disabled:opacity-60">
                  {actionLoading === 'close' && <Loader2 className="w-4 h-4 animate-spin" />}
                  Close Bidding
                </button>
              )}
              {['DRAFT', 'OPEN', 'UNDER_REVIEW'].includes(rfq.status) && (
                <button id="cancel-btn" onClick={() => doAction('cancel')} disabled={!!actionLoading}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-lg border border-red-300 text-red-600 text-sm font-medium hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors disabled:opacity-60">
                  {actionLoading === 'cancel' && <Loader2 className="w-4 h-4 animate-spin" />}
                  <XCircle className="w-4 h-4" /> Cancel
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-sm text-red-600 dark:text-red-400">
          <ShieldAlert className="w-4 h-4 inline mr-1.5" /> {error}
        </div>
      )}

      {/* Line Items */}
      <div className="glass-card p-6">
        <h3 className="font-semibold text-gray-800 dark:text-white mb-4 flex items-center gap-2">
          <Package className="w-4 h-4 text-blue-500" /> Line Items ({rfq.items.length})
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 dark:border-gray-700 text-left text-xs text-gray-400 uppercase tracking-wide">
                <th className="pb-2 font-medium">Code</th>
                <th className="pb-2 font-medium">Description</th>
                <th className="pb-2 font-medium text-right">Qty</th>
                <th className="pb-2 font-medium">UOM</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50 dark:divide-gray-800">
              {rfq.items.map((item) => (
                <tr key={item.id} className="hover:bg-gray-50/50 dark:hover:bg-gray-800/50">
                  <td className="py-2.5 pr-4 font-mono text-xs text-blue-600 dark:text-blue-400">{item.item_code}</td>
                  <td className="py-2.5 pr-4 text-gray-700 dark:text-gray-300">{item.description}</td>
                  <td className="py-2.5 pr-4 text-right font-semibold">{item.required_quantity}</td>
                  <td className="py-2.5 text-gray-400">{item.unit_of_measure}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Vendor: Quote submission */}
      {canSubmitQuote && (
        <div className="glass-card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-800 dark:text-white flex items-center gap-2">
              <Trophy className="w-4 h-4 text-yellow-500" /> Submit Your Quote
            </h3>
            <button onClick={() => setShowQuoteForm(!showQuoteForm)} className="text-sm text-blue-600 hover:underline">
              {showQuoteForm ? 'Hide form' : 'Fill quote'}
            </button>
          </div>

          {showQuoteForm && (
            <div className="space-y-4">
              {rfq.items.map((item) => (
                <div key={item.id} className="border border-gray-100 dark:border-gray-700 rounded-xl p-4">
                  <p className="text-xs font-semibold text-gray-400 mb-3 uppercase">{item.item_code} — {item.description}</p>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Unit Price *</label>
                      <input type="number" min="0.01" step="0.01" placeholder="0.00"
                        value={quoteInputs[item.id]?.unit_price ?? ''}
                        onChange={(e) => setQuoteInputs((p) => ({ ...p, [item.id]: { ...p[item.id], unit_price: e.target.value } }))}
                        className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white/50 dark:bg-gray-800/50 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm" />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Lead Time (days) *</label>
                      <input type="number" min="1" placeholder="14"
                        value={quoteInputs[item.id]?.lead_time_days ?? ''}
                        onChange={(e) => setQuoteInputs((p) => ({ ...p, [item.id]: { ...p[item.id], lead_time_days: e.target.value } }))}
                        className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white/50 dark:bg-gray-800/50 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm" />
                    </div>
                  </div>
                  <div className="mt-2">
                    <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Notes</label>
                    <input type="text" placeholder="Optional notes..."
                      value={quoteInputs[item.id]?.notes ?? ''}
                      onChange={(e) => setQuoteInputs((p) => ({ ...p, [item.id]: { ...p[item.id], notes: e.target.value } }))}
                      className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white/50 dark:bg-gray-800/50 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm" />
                  </div>
                </div>
              ))}
              <button id="submit-quote-btn" onClick={submitQuote} disabled={actionLoading === 'quote'}
                className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-sm font-semibold hover:from-blue-700 hover:to-indigo-700 transition-all disabled:opacity-60">
                {actionLoading === 'quote' && <Loader2 className="w-4 h-4 animate-spin" />}
                Submit Quote
              </button>
            </div>
          )}
        </div>
      )}

      {hasSubmittedQuote && (
        <div className="glass-card p-4 flex items-center gap-3 bg-green-50/50 dark:bg-green-900/10 border border-green-200 dark:border-green-800">
          <CheckCircle className="w-5 h-5 text-green-600" />
          <div>
            <p className="text-sm font-semibold text-green-700 dark:text-green-400">Quote submitted</p>
            <p className="text-xs text-green-600/70 dark:text-green-400/70">
              Total: {rfq.currency_code} {quotes[0]?.total_bid_amount.toFixed(2)}
            </p>
          </div>
        </div>
      )}

      {/* Buyer: Quote comparison */}
      {isBuyer && quotes.length > 0 && (
        <div className="glass-card p-6">
          <h3 className="font-semibold text-gray-800 dark:text-white mb-4 flex items-center gap-2">
            <Trophy className="w-4 h-4 text-yellow-500" /> Received Quotes ({quotes.length})
          </h3>
          <div className="space-y-3">
            {quotes.map((q) => (
              <div key={q.id} className={`border rounded-xl p-4 transition-colors ${
                q.status === 'AWARDED' ? 'border-blue-300 dark:border-blue-700 bg-blue-50/50 dark:bg-blue-900/20' :
                q.status === 'REJECTED' ? 'border-gray-100 dark:border-gray-800 opacity-60' :
                'border-gray-200 dark:border-gray-700'
              }`}>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-gray-400 font-mono">{q.id.slice(0, 8)}…</p>
                    <p className="font-semibold text-lg text-gray-900 dark:text-white">
                      {rfq.currency_code} {q.total_bid_amount.toFixed(2)}
                    </p>
                    <span className={`inline-block mt-1 text-xs px-2 py-0.5 rounded-full font-medium ${
                      q.status === 'AWARDED' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300' :
                      q.status === 'REJECTED' ? 'bg-gray-100 text-gray-500' : 'bg-green-100 text-green-700'
                    }`}>{q.status}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <button onClick={() => setExpandedQuote(expandedQuote === q.id ? null : q.id)}
                      className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-400 transition-colors">
                      {expandedQuote === q.id ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>
                    {rfq.status === 'UNDER_REVIEW' && q.status === 'SUBMITTED' && (
                      <button id={`award-${q.id}`} onClick={() => awardQuote(q.id)}
                        disabled={actionLoading === `award-${q.id}`}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600 text-white text-xs font-semibold hover:bg-blue-700 transition-colors disabled:opacity-60">
                        {actionLoading === `award-${q.id}` && <Loader2 className="w-3 h-3 animate-spin" />}
                        <Trophy className="w-3 h-3" /> Award
                      </button>
                    )}
                    {q.status === 'AWARDED' && <Trophy className="w-5 h-5 text-yellow-500" />}
                  </div>
                </div>

                {expandedQuote === q.id && (
                  <div className="mt-4 border-t border-gray-100 dark:border-gray-700 pt-4">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="text-gray-400 uppercase tracking-wide text-left">
                          <th className="pb-1 font-medium">Item ID</th>
                          <th className="pb-1 font-medium text-right">Unit Price</th>
                          <th className="pb-1 font-medium text-right">Lead Time</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-50 dark:divide-gray-800">
                        {q.items.map((qi) => (
                          <tr key={qi.id}>
                            <td className="py-1.5 font-mono text-gray-500">{qi.rfq_item_id.slice(0, 8)}…</td>
                            <td className="py-1.5 text-right font-semibold">{rfq.currency_code} {qi.unit_price.toFixed(2)}</td>
                            <td className="py-1.5 text-right text-gray-400">{qi.lead_time_days}d</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Clarifications Q&A */}
      <div className="glass-card p-6">
        <h3 className="font-semibold text-gray-800 dark:text-white mb-4 flex items-center gap-2">
          <MessageSquare className="w-4 h-4 text-purple-500" /> Clarifications ({clarifications.length})
        </h3>

        <div className="space-y-3 mb-4">
          {clarifications.length === 0 && (
            <p className="text-sm text-gray-400 text-center py-4">No questions yet.</p>
          )}
          {clarifications.map((c) => (
            <div key={c.id} className="border border-gray-100 dark:border-gray-700 rounded-xl p-4 space-y-2">
              <div className="flex items-start justify-between gap-2">
                <p className="text-sm font-medium text-gray-800 dark:text-gray-200">
                  {c.asked_by_vendor_id ? `Vendor ${c.asked_by_vendor_id.slice(0, 6)}…` : 'Anonymous Vendor'}
                </p>
                <span className="text-xs text-gray-400">{new Date(c.created_at).toLocaleDateString()}</span>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Q: {c.question}</p>
              {c.answer ? (
                <div className="flex items-start gap-2 p-2.5 rounded-lg bg-blue-50 dark:bg-blue-900/20">
                  <CheckCircle className="w-3.5 h-3.5 text-blue-500 mt-0.5 shrink-0" />
                  <p className="text-xs text-blue-700 dark:text-blue-300">{c.answer}</p>
                </div>
              ) : (
                isBuyer && rfq.buyer_id === user?.id && (
                  <div className="flex gap-2 mt-2">
                    <input
                      type="text"
                      placeholder="Type your answer..."
                      value={answerInputs[c.id] ?? ''}
                      onChange={(e) => setAnswerInputs((p) => ({ ...p, [c.id]: e.target.value }))}
                      className="flex-1 px-3 py-1.5 rounded-lg border border-gray-200 dark:border-gray-700 bg-white/50 dark:bg-gray-800/50 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                    />
                    <button onClick={() => answerClarification(c.id)}
                      disabled={actionLoading === `ans-${c.id}`}
                      className="px-3 py-1.5 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 disabled:opacity-60">
                      {actionLoading === `ans-${c.id}` ? <Loader2 className="w-3 h-3 animate-spin" /> : <Send className="w-3 h-3" />}
                    </button>
                  </div>
                )
              )}
            </div>
          ))}
        </div>

        {/* Vendor: ask question */}
        {isVendor && rfq.status === 'OPEN' && (
          <div className="flex gap-2">
            <input
              type="text"
              id="clarification-input"
              placeholder="Ask a clarification question..."
              value={clarQuestion}
              onChange={(e) => setClarQuestion(e.target.value)}
              className="flex-1 px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white/50 dark:bg-gray-800/50 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            />
            <button id="ask-clar-btn" onClick={askClarification} disabled={actionLoading === 'clar' || !clarQuestion.trim()}
              className="px-4 py-2 rounded-lg bg-purple-600 text-white text-sm font-medium hover:bg-purple-700 disabled:opacity-60 transition-colors flex items-center gap-1.5">
              {actionLoading === 'clar' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
              Ask
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
