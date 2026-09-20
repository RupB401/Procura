import React, { useState } from 'react';
import { api } from '../lib/api';
import type { RFQ } from '../lib/types';
import { Plus, Trash2, ArrowLeft, Loader2 } from 'lucide-react';

interface RFQItemForm {
  item_code: string;
  description: string;
  required_quantity: string;
  unit_of_measure: string;
}

interface CreateRFQPageProps {
  onBack: () => void;
  onCreated: (rfq: RFQ) => void;
}

export function CreateRFQPage({ onBack, onCreated }: CreateRFQPageProps) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [deliveryLocation, setDeliveryLocation] = useState('');
  const [deadline, setDeadline] = useState('');
  const [currency, setCurrency] = useState('USD');
  const [items, setItems] = useState<RFQItemForm[]>([
    { item_code: '', description: '', required_quantity: '', unit_of_measure: 'PCS' },
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const addItem = () =>
    setItems([...items, { item_code: '', description: '', required_quantity: '', unit_of_measure: 'PCS' }]);

  const removeItem = (i: number) => setItems(items.filter((_, idx) => idx !== i));

  const updateItem = (i: number, field: keyof RFQItemForm, value: string) =>
    setItems(items.map((item, idx) => (idx === i ? { ...item, [field]: value } : item)));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);
    try {
      const rfq = await api.post<RFQ>('/rfqs', {
        title,
        description: description || undefined,
        delivery_location: deliveryLocation,
        submission_deadline: new Date(deadline).toISOString(),
        currency_code: currency,
        items: items.map((item) => ({
          ...item,
          required_quantity: parseFloat(item.required_quantity),
        })),
      });
      onCreated(rfq);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to create RFQ');
    } finally {
      setIsLoading(false);
    }
  };

  const inputCls = 'w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white/50 dark:bg-gray-800/50 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm';
  const labelCls = 'block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1';

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <button onClick={onBack} className="flex items-center gap-1.5 text-sm text-gray-500 dark:text-gray-400 hover:text-blue-600 mb-6">
        <ArrowLeft className="w-4 h-4" /> Back to list
      </button>

      <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">Create New RFQ</h2>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Info */}
        <div className="glass-card p-6 space-y-4">
          <h3 className="font-semibold text-gray-800 dark:text-white">Basic Information</h3>

          <div>
            <label className={labelCls}>Title *</label>
            <input id="rfq-title" type="text" value={title} onChange={(e) => setTitle(e.target.value)}
              required className={inputCls} placeholder="e.g. Office Supplies Q3 2026" />
          </div>

          <div>
            <label className={labelCls}>Description</label>
            <textarea value={description} onChange={(e) => setDescription(e.target.value)}
              rows={3} className={inputCls} placeholder="Additional context for vendors..." />
          </div>

          <div>
            <label className={labelCls}>Delivery Location *</label>
            <input type="text" value={deliveryLocation} onChange={(e) => setDeliveryLocation(e.target.value)}
              required className={inputCls} placeholder="e.g. New York Warehouse, or EXW" />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className={labelCls}>Submission Deadline *</label>
              <input id="rfq-deadline" type="datetime-local" value={deadline} onChange={(e) => setDeadline(e.target.value)}
                required className={inputCls} />
            </div>
            <div>
              <label className={labelCls}>Currency</label>
              <select value={currency} onChange={(e) => setCurrency(e.target.value)} className={inputCls}>
                {['USD', 'EUR', 'GBP', 'INR', 'CAD', 'AUD'].map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Line Items */}
        <div className="glass-card p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-gray-800 dark:text-white">Line Items</h3>
            <button type="button" onClick={addItem}
              className="flex items-center gap-1.5 text-sm text-blue-600 hover:text-blue-700 font-medium">
              <Plus className="w-4 h-4" /> Add Item
            </button>
          </div>

          {items.map((item, i) => (
            <div key={i} className="border border-gray-200 dark:border-gray-700 rounded-xl p-4 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-gray-400 uppercase tracking-wide">Item {i + 1}</span>
                {items.length > 1 && (
                  <button type="button" onClick={() => removeItem(i)}
                    className="text-red-400 hover:text-red-600 transition-colors">
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className={labelCls}>Item Code *</label>
                  <input type="text" value={item.item_code}
                    onChange={(e) => updateItem(i, 'item_code', e.target.value)}
                    required className={inputCls} placeholder="SKU-001" />
                </div>
                <div>
                  <label className={labelCls}>Unit of Measure *</label>
                  <select value={item.unit_of_measure}
                    onChange={(e) => updateItem(i, 'unit_of_measure', e.target.value)} className={inputCls}>
                    {['PCS', 'KG', 'LTR', 'MTR', 'BOX', 'SET', 'UNIT'].map((u) => (
                      <option key={u} value={u}>{u}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div>
                <label className={labelCls}>Description *</label>
                <input type="text" value={item.description}
                  onChange={(e) => updateItem(i, 'description', e.target.value)}
                  required className={inputCls} placeholder="Detailed item description" />
              </div>
              <div>
                <label className={labelCls}>Required Quantity *</label>
                <input type="number" min="0.01" step="0.01" value={item.required_quantity}
                  onChange={(e) => updateItem(i, 'required_quantity', e.target.value)}
                  required className={inputCls} placeholder="100" />
              </div>
            </div>
          ))}
        </div>

        {error && (
          <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-sm text-red-600 dark:text-red-400">
            {error}
          </div>
        )}

        <div className="flex gap-3">
          <button type="button" onClick={onBack}
            className="flex-1 py-2.5 rounded-lg border border-gray-200 dark:border-gray-700 text-sm font-medium text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
            Cancel
          </button>
          <button id="submit-rfq" type="submit" disabled={isLoading}
            className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-sm font-semibold hover:from-blue-700 hover:to-indigo-700 transition-all disabled:opacity-60 disabled:cursor-not-allowed">
            {isLoading && <Loader2 className="w-4 h-4 animate-spin" />}
            Save as Draft
          </button>
        </div>
      </form>
    </div>
  );
}
