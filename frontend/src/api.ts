import axios from 'axios'
import type { FactorPayload, HistoryPoint, MarketOverview, PredictionResponse } from './types'

const client = axios.create({ baseURL: '' })

export async function fetchOverview() {
  const { data } = await client.get<MarketOverview>('/api/market/overview')
  return data
}

export async function fetchHistory(limit = 120) {
  const { data } = await client.get<HistoryPoint[]>('/api/btc/history', { params: { limit } })
  return data
}

export async function fetchFactors() {
  const { data } = await client.get<FactorPayload>('/api/factors')
  return data
}

export async function predict(model_name = 'xgboost', horizon_days = 7) {
  const { data } = await client.post<PredictionResponse>('/api/predict', {
    symbol: 'BTC',
    model_name,
    horizon_days,
  })
  return data
}
