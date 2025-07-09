
// User and Authentication Types
export interface User {
  id: string
  email: string
  name: string
  role: 'admin' | 'user' | 'accountant'
  company_id?: string
  created_at: string
  updated_at: string
}

export interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
}

// Accounting Types
export interface Transaction {
  id: string
  date: string
  description: string
  amount: number
  type: 'debit' | 'credit'
  account: string
  category: string
  reference?: string
  processed: boolean
}

export interface AccountingData {
  transactions: Transaction[]
  summary: {
    total_debits: number
    total_credits: number
    balance: number
    transaction_count: number
  }
}

// Bank Reconciliation Types
export interface BankTransaction {
  id: string
  date: string
  description: string
  amount: number
  type: 'debit' | 'credit'
  balance: number
  reference?: string
  matched: boolean
  confidence_score?: number
}

export interface ReconciliationMatch {
  bank_transaction_id: string
  ledger_transaction_id: string
  confidence_score: number
  match_type: 'exact' | 'partial' | 'manual'
  created_at: string
}

// Report Types
export interface FinancialReport {
  id: string
  name: string
  type: 'balance_sheet' | 'income_statement' | 'cash_flow' | 'trial_balance'
  period_start: string
  period_end: string
  data: Record<string, any>
  created_at: string
}

// File Upload Types
export interface UploadProgress {
  loaded: number
  total: number
  percentage: number
}

export interface FileUpload {
  file: File
  progress: UploadProgress
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'error'
  result?: any
  error?: string
}

// Dashboard Types
export interface DashboardMetrics {
  total_transactions: number
  pending_reconciliations: number
  recent_reports: number
  system_health: 'good' | 'warning' | 'error'
}

// Form Types
export interface LoginForm {
  email: string
  password: string
}

export interface RegisterForm {
  name: string
  email: string
  password: string
  confirmPassword: string
  company?: string
}

// API Response Types
export interface ApiResponse<T = any> {
  data: T
  message?: string
  success: boolean
  errors?: Record<string, string[]>
}

// Chart Data Types
export interface ChartData {
  labels: string[]
  datasets: {
    label: string
    data: number[]
    backgroundColor?: string | string[]
    borderColor?: string | string[]
    borderWidth?: number
  }[]
}

// Navigation Types
export interface NavItem {
  label: string
  href: string
  icon?: string
  children?: NavItem[]
  requiresAuth?: boolean
  roles?: string[]
}
export interface User {
  id: string
  username: string
  email: string
  firstName: string
  lastName: string
  role: string
  isActive: boolean
}

export interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
}
