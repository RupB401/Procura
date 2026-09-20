// Shared TypeScript types matching backend Pydantic schemas

export type UserRole = 'BUYER' | 'VENDOR';

export interface User {
  id: string;
  email: string;
  company_name: string;
  role: UserRole;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export type RFQStatus = 'DRAFT' | 'OPEN' | 'UNDER_REVIEW' | 'AWARDED' | 'CANCELLED';
export type QuoteStatus = 'SUBMITTED' | 'AWARDED' | 'REJECTED';

export interface RFQItem {
  id: string;
  rfq_id: string;
  item_code: string;
  description: string;
  required_quantity: number;
  unit_of_measure: string;
}

export interface RFQ {
  id: string;
  buyer_id: string;
  title: string;
  description: string | null;
  status: RFQStatus;
  submission_deadline: string;
  currency_code: string;
  created_at: string;
  updated_at: string;
  items: RFQItem[];
}

export interface RFQListItem {
  id: string;
  buyer_id: string;
  title: string;
  status: RFQStatus;
  submission_deadline: string;
  currency_code: string;
  created_at: string;
}

export interface QuoteItem {
  id: string;
  rfq_item_id: string;
  unit_price: number;
  lead_time_days: number;
  min_order_quantity: number;
  notes: string | null;
}

export interface Quote {
  id: string;
  rfq_id: string;
  vendor_id: string;
  status: QuoteStatus;
  total_bid_amount: number;
  submitted_at: string;
  items: QuoteItem[];
}

export interface Clarification {
  id: string;
  rfq_id: string;
  asked_by_vendor_id: string | null;
  question: string;
  answer: string | null;
  is_broadcast: boolean;
  created_at: string;
  answered_at: string | null;
}
