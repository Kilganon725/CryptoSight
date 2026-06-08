export interface MarketOverview {
  symbol: string
  current_price: number
  change_24h: number
  volume_24h: number
  market_cap?: number | null
  as_of: string
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
