import axios from 'axios'
import type {
  FactorPayload,
  HistoryPoint,
  MarketOverview,
  OKXInstrument,
  OrderbookSnapshot,
  PredictionResponse,
  RecentTrade,
} from './types'

const client = axios.create({ baseURL: '' })

export async function fetchOverview(inst_id = 'BTC-USDT') {
  const { data } = await client.get<MarketOverview>('/api/market/overview', { params: { inst_id } })
  return data
}

export async function fetchHistory(limit = 120, bar = '1D', inst_id = 'BTC-USDT') {
  const { data } = await client.get<HistoryPoint[]>('/api/btc/history', { params: { limit, bar, inst_id } })
  return data
}

export async function fetchFactors(symbol = 'BTC', inst_id = 'BTC-USDT') {
  const { data } = await client.get<FactorPayload>('/api/factors', { params: { symbol, inst_id } })
  return data
}

export async function fetchInstrument(inst_id = 'BTC-USDT') {
  const { data } = await client.get<OKXInstrument>('/api/market/instrument', { params: { inst_id } })
  return data
}

export async function fetchOrderbook(inst_id = 'BTC-USDT', depth = 20) {
  const { data } = await client.get<OrderbookSnapshot>('/api/market/orderbook', { params: { inst_id, depth } })
  return data
}

export async function fetchTrades(inst_id = 'BTC-USDT', limit = 20) {
  const { data } = await client.get<RecentTrade[]>('/api/market/trades', { params: { inst_id, limit } })
  return data
}

export async function predict(model_name = 'xgboost', horizon_days = 7, symbol = 'BTC', inst_id = 'BTC-USDT') {
  const { data } = await client.post<PredictionResponse>('/api/predict', {
    symbol,
    inst_id,
    model_name,
    horizon_days,
  })
  return data
}
