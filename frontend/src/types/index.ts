export interface User {
  id: number;
  email: string;
  username: string;
  full_name?: string;
  is_active: boolean;
  subscription_tier: string;
}

export interface TradingBot {
  id: number;
  name: string;
  description?: string;
  exchange: string;
  trading_pair: string;
  status: 'stopped' | 'running' | 'paused' | 'error';
  initial_capital: number;
  current_capital: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  total_profit_loss: number;
  created_at: string;
  started_at?: string;
}

export interface Strategy {
  id: number;
  name: string;
  description?: string;
  strategy_type: 'ai' | 'technical' | 'hybrid';
  parameters: Record<string, any>;
  is_active: boolean;
  is_public: boolean;
  sharpe_ratio?: number;
  max_drawdown?: number;
  win_rate?: number;
  created_at: string;
}

export interface Order {
  id: number;
  symbol: string;
  side: string;
  order_type: string;
  quantity: number;
  price?: number;
  status: string;
  filled_quantity: number;
  created_at: string;
}

export interface Trade {
  id: number;
  symbol: string;
  entry_price: number;
  exit_price?: number;
  quantity: number;
  profit_loss?: number;
  profit_loss_percentage?: number;
  is_open: boolean;
  entry_time: string;
  exit_time?: string;
}

export interface Candle {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}
