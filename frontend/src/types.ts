export interface MarketOverview {
  symbol: string
  current_price: number
  change_24h: number
  volume_24h: number
  market_cap?: number | null
  as_of: string
}

export interface OKXInstrument {
  inst_id: string
  base_ccy?: string | null
  quote_ccy?: string | null
  tick_sz?: string | null
  lot_sz?: string | null
  min_sz?: string | null
  ct_val?: string | null
  ct_mult?: string | null
  state?: string | null
  source?: string
}

export interface HistoryPoint {
  ts: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  market_cap?: number | null
}

export interface FactorPayload {
  correlations: Record<string, unknown>
  causality: Record<string, unknown>
  feature_importance: Array<{ feature: string; importance: number; rank: number }>
  shap_summary: Array<{ feature: string; shap_value: number; rank: number }>
}

export interface PredictionResponse {
  symbol: string
  model_name: string
  horizon_days: number
  predicted_price: number
  confidence_score: number
  metrics: Record<string, number>
  as_of: string
}

export interface OrderbookLevel {
  price: number
  size: number
  orders: number
}

export interface OrderbookSnapshot {
  inst_id: string
  ts: string
  seq_id?: number | string
  asks: OrderbookLevel[]
  bids: OrderbookLevel[]
  source?: string
}

export interface RecentTrade {
  inst_id: string
  trade_id?: string | number
  price: number
  size: number
  side?: string | null
  ts: string
  source?: string
}
