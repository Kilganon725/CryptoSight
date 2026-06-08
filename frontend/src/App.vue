<template>
  <div class="shell">
    <section class="hero">
      <div class="hero-copy">
        <div class="eyebrow">CryptoSight / BTC Market Terminal</div>
        <h1>BTC Market Terminal</h1>
        <p>
          Switch between minute, hour, day, week, and month K-lines. Inspect candlesticks, volume, MA, MACD, RSI,
          and the factor-analysis stack in one unified view.
        </p>
        <div class="hero-badges">
          <span class="badge">Live OKX candles</span>
          <span class="badge">Social sentiment pipeline</span>
          <span class="badge">Model comparison</span>
        </div>
      </div>

      <div class="hero-stats">
        <div class="stat-card">
          <span>{{ selectedPairLabel }} Price</span>
          <strong>{{ formatPrice(overview?.current_price ?? latestClose) }}</strong>
        </div>
        <div class="stat-card">
          <span>24h Change</span>
          <strong :class="changeClass">{{ formatChange(overview?.change_24h) }}</strong>
        </div>
        <div class="stat-card">
          <span>24h Volume</span>
          <strong>{{ formatVolume(overview?.volume_24h ?? latestVolume) }}</strong>
        </div>
      </div>
    </section>

    <main class="workspace">
      <section class="panel chart-panel">
        <div class="panel-head chart-head">
          <div>
            <h2>{{ selectedPairLabel }} Chart</h2>
            <div class="subline">
              {{ selectedIntervalLabel }} · {{ chartTypeLabel }} · {{ indicatorLabel }}
            </div>
          </div>

          <div class="chart-actions">
            <el-select v-model="selectedPair" size="small" class="pair-select">
              <el-option v-for="pair in pairOptions" :key="pair.value" :label="pair.label" :value="pair.value" />
            </el-select>
            <div class="interval-group">
              <button
                v-for="item in intervalOptions"
                :key="item.value"
                class="interval-btn"
                :class="{ active: selectedInterval === item.value }"
                @click="selectedInterval = item.value"
              >
                {{ item.label }}
              </button>
            </div>

            <el-radio-group v-model="chartMode" size="small" class="mode-group">
              <el-radio-button label="candlestick">K-line</el-radio-button>
              <el-radio-button label="line">Line</el-radio-button>
            </el-radio-group>

            <el-radio-group v-model="indicatorMode" size="small" class="mode-group">
              <el-radio-button label="macd">MACD</el-radio-button>
              <el-radio-button label="rsi">RSI</el-radio-button>
            </el-radio-group>
          </div>
        </div>

        <div class="chart-summary">
          <div class="summary-chip">
            <span>Open</span>
            <strong>{{ formatPrice(latestCandle?.open) }}</strong>
          </div>
          <div class="summary-chip">
            <span>High</span>
            <strong>{{ formatPrice(latestCandle?.high) }}</strong>
          </div>
          <div class="summary-chip">
            <span>Low</span>
            <strong>{{ formatPrice(latestCandle?.low) }}</strong>
          </div>
          <div class="summary-chip">
            <span>Close</span>
            <strong :class="priceDirectionClass">{{ formatPrice(latestCandle?.close) }}</strong>
          </div>
          <div class="summary-chip">
            <span>Volume</span>
            <strong>{{ formatVolume(latestCandle?.volume) }}</strong>
          </div>
          <div class="summary-chip">
            <span>As Of</span>
            <strong>{{ latestTimestamp }}</strong>
          </div>
        </div>

        <div ref="trendEl" v-loading="loadingHistory" class="trend-chart"></div>
      </section>

      <aside class="panel side-panel">
        <div class="panel-head">
          <h2>{{ selectedPairLabel }} Snapshot</h2>
          <span>Live feed</span>
        </div>

        <div class="snapshot-grid">
          <div class="snapshot-item">
            <span>Interval</span>
            <strong>{{ selectedIntervalLabel }}</strong>
          </div>
          <div class="snapshot-item">
            <span>Bars</span>
            <strong>{{ history.length }}</strong>
          </div>
          <div class="snapshot-item">
            <span>Trend</span>
            <strong :class="priceDirectionClass">{{ priceDirectionText }}</strong>
          </div>
          <div class="snapshot-item">
            <span>Confidence</span>
            <strong>{{ prediction ? `${(prediction.confidence_score * 100).toFixed(2)}%` : '--' }}</strong>
          </div>
        </div>

        <div class="mini-metrics">
          <div class="metric-row">
            <span>Latest Close</span>
            <strong>{{ formatPrice(latestClose) }}</strong>
          </div>
          <div class="metric-row">
            <span>Average Volume</span>
            <strong>{{ formatVolume(averageVolume) }}</strong>
          </div>
          <div class="metric-row">
            <span>High / Low</span>
            <strong>{{ formatPrice(highestHigh) }} / {{ formatPrice(lowestLow) }}</strong>
          </div>
          <div class="metric-row">
            <span>Model</span>
            <strong>{{ prediction?.model_name ?? 'xgboost' }}</strong>
          </div>
        </div>

        <div class="orderbook-section">
          <div class="panel-head compact">
            <h3>Order Book</h3>
            <span>{{ instrument?.tick_sz ? `tick ${instrument.tick_sz}` : 'live' }}</span>
          </div>
          <div class="orderbook-grid">
            <div class="orderbook-column asks">
              <div class="orderbook-title">Asks</div>
              <div v-for="level in askLevels" :key="`ask-${level.price}-${level.size}`" class="orderbook-row">
                <span class="price">{{ formatPrice(level.price) }}</span>
                <span class="size">{{ formatAmount(level.size) }}</span>
              </div>
            </div>
            <div class="orderbook-column bids">
              <div class="orderbook-title">Bids</div>
              <div v-for="level in bidLevels" :key="`bid-${level.price}-${level.size}`" class="orderbook-row">
                <span class="price">{{ formatPrice(level.price) }}</span>
                <span class="size">{{ formatAmount(level.size) }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="trade-section">
          <div class="panel-head compact">
            <h3>Recent Trades</h3>
            <span>{{ recentTrades.length }}</span>
          </div>
          <div class="trade-list">
            <div v-for="trade in recentTrades" :key="`${trade.trade_id}-${trade.ts}`" class="trade-row" :class="trade.side">
              <span class="time">{{ formatTradeTime(trade.ts) }}</span>
              <span class="side">{{ trade.side }}</span>
              <span class="price">{{ formatPrice(trade.price) }}</span>
              <span class="size">{{ formatAmount(trade.size) }}</span>
            </div>
          </div>
        </div>

        <div class="panel-inner">
          <div class="panel-head compact">
            <h3>Prediction Center</h3>
            <span>API-backed</span>
          </div>
          <div class="controls">
            <el-select v-model="modelName" class="control" placeholder="Model">
              <el-option label="XGBoost" value="xgboost" />
              <el-option label="Random Forest" value="random_forest" />
              <el-option label="ARIMA" value="arima" />
              <el-option label="Prophet" value="prophet" />
              <el-option label="LSTM" value="lstm" />
            </el-select>
            <el-select v-model="horizonDays" class="control" placeholder="Horizon">
              <el-option label="1 Day" :value="1" />
              <el-option label="3 Days" :value="3" />
              <el-option label="7 Days" :value="7" />
              <el-option label="30 Days" :value="30" />
            </el-select>
            <el-button type="primary" class="predict-btn" :loading="predicting" @click="runPrediction">
              Predict
            </el-button>
          </div>

          <div v-if="prediction" class="prediction-box">
            <div class="prediction-price">{{ formatPrice(prediction.predicted_price) }}</div>
            <div class="prediction-meta">{{ prediction.model_name }} · {{ prediction.horizon_days }} day horizon</div>
            <div class="prediction-meta">Confidence: {{ (prediction.confidence_score * 100).toFixed(2) }}%</div>
            <div class="metrics">
              <div v-for="(value, key) in prediction.metrics" :key="key" class="metric-item">
                <span>{{ key.toUpperCase() }}</span>
                <strong>{{ value.toFixed(4) }}</strong>
              </div>
            </div>
          </div>
        </div>
      </aside>

      <section class="panel panel-wide">
        <div class="panel-head">
          <h2>Factor Analysis</h2>
          <span>Correlation · Feature importance · SHAP</span>
        </div>
        <div class="factor-grid">
          <div class="factor-card">
            <h3>Top Factors</h3>
            <div class="rank-list">
              <div v-for="item in topFactors" :key="item.feature" class="rank-item">
                <span>#{{ item.rank }}</span>
                <strong>{{ item.feature }}</strong>
                <em>{{ item.importance.toFixed(4) }}</em>
              </div>
            </div>
          </div>
          <div class="factor-card">
            <h3>Macro Signals</h3>
            <div class="mini-grid two-col">
              <div class="mini-card" v-for="item in macroHighlights" :key="item.label">
                <span>{{ item.label }}</span>
                <strong>{{ item.value }}</strong>
              </div>
            </div>
          </div>
          <div class="factor-card">
            <h3>Sentiment Signals</h3>
            <div class="mini-grid two-col">
              <div class="mini-card" v-for="item in sentimentHighlights" :key="item.label">
                <span>{{ item.label }}</span>
                <strong>{{ item.value }}</strong>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class="panel panel-wide">
        <div class="panel-head">
          <h2>Research Notes</h2>
          <span>Thesis-ready outputs</span>
        </div>
        <el-alert
          title="The trading chart now supports real interval switching, candlesticks, MA, volume, MACD, and RSI."
          type="success"
          :closable="false"
          show-icon
        />
        <div class="notes">
          <div>
            <strong>Research question</strong>
            <p>Which factors most strongly affect cryptocurrency prices, and does multi-source data improve prediction accuracy?</p>
          </div>
          <div>
            <strong>Next expansion</strong>
            <p>Connect additional pairs like ETH/USDT and add order-book depth, support/resistance, and signal annotations.</p>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { fetchFactors, fetchHistory, fetchInstrument, fetchOrderbook, fetchOverview, fetchTrades, predict } from './api'
import type {
  FactorPayload,
  HistoryPoint,
  MarketOverview,
  OKXInstrument,
  OrderbookSnapshot,
  PredictionResponse,
  RecentTrade,
} from './types'

type IntervalKey = '1m' | '5m' | '15m' | '1H' | '4H' | '1D' | '1W' | '1M'
type ChartMode = 'candlestick' | 'line'
type IndicatorMode = 'macd' | 'rsi'
type PairKey = 'BTC-USDT' | 'ETH-USDT'

const pairOptions: Array<{ label: string; value: PairKey; symbol: 'BTC' | 'ETH' }> = [
  { label: 'BTC/USDT', value: 'BTC-USDT', symbol: 'BTC' },
  { label: 'ETH/USDT', value: 'ETH-USDT', symbol: 'ETH' },
]

const intervalOptions: Array<{ label: string; value: IntervalKey; limit: number }> = [
  { label: '1m', value: '1m', limit: 300 },
  { label: '5m', value: '5m', limit: 300 },
  { label: '15m', value: '15m', limit: 300 },
  { label: '1H', value: '1H', limit: 240 },
  { label: '4H', value: '4H', limit: 240 },
  { label: '1D', value: '1D', limit: 240 },
  { label: '1W', value: '1W', limit: 180 },
  { label: '1M', value: '1M', limit: 120 },
]

const overview = ref<MarketOverview | null>(null)
const history = ref<HistoryPoint[]>([])
const factors = ref<FactorPayload | null>(null)
const instrument = ref<OKXInstrument | null>(null)
const orderbook = ref<OrderbookSnapshot | null>(null)
const recentTrades = ref<RecentTrade[]>([])
const prediction = ref<PredictionResponse | null>(null)
const selectedPair = ref<PairKey>('BTC-USDT')
const selectedInterval = ref<IntervalKey>('1H')
const chartMode = ref<ChartMode>('candlestick')
const indicatorMode = ref<IndicatorMode>('macd')
const modelName = ref('xgboost')
const horizonDays = ref(7)
const loadingHistory = ref(false)
const predicting = ref(false)

const trendEl = ref<HTMLDivElement | null>(null)
let trendChart: echarts.ECharts | null = null
let feedTimer: number | null = null

const changeClass = computed(() => {
  const change = overview.value?.change_24h ?? 0
  return change >= 0 ? 'positive' : 'negative'
})

const selectedPairLabel = computed(() => pairOptions.find((item) => item.value === selectedPair.value)?.label ?? selectedPair.value)
const selectedPairSymbol = computed(() => pairOptions.find((item) => item.value === selectedPair.value)?.symbol ?? 'BTC')
const priceDecimals = computed(() => {
  const tick = instrument.value?.tick_sz
  if (!tick || !tick.includes('.')) return 2
  return Math.min(8, tick.split('.')[1].replace(/0+$/, '').length || 2)
})
const orderbookDepth = computed(() => {
  const asks = orderbook.value?.asks ?? []
  const bids = orderbook.value?.bids ?? []
  return Math.min(8, Math.max(asks.length, bids.length))
})
const askLevels = computed(() => (orderbook.value?.asks ?? []).slice(0, orderbookDepth.value))
const bidLevels = computed(() => (orderbook.value?.bids ?? []).slice(0, orderbookDepth.value))

const latestCandle = computed(() => history.value.at(-1) ?? null)
const previousCandle = computed(() => history.value.length > 1 ? history.value.at(-2) ?? null : null)
const latestClose = computed(() => latestCandle.value?.close ?? 0)
const latestVolume = computed(() => latestCandle.value?.volume ?? 0)
const latestTimestamp = computed(() => latestCandle.value?.ts ? formatDateTime(latestCandle.value.ts) : '--')
const highestHigh = computed(() => history.value.length ? Math.max(...history.value.map((item) => item.high)) : 0)
const lowestLow = computed(() => history.value.length ? Math.min(...history.value.map((item) => item.low)) : 0)
const averageVolume = computed(() => history.value.length ? history.value.reduce((sum, item) => sum + item.volume, 0) / history.value.length : 0)
const priceDirectionClass = computed(() => {
  if (!latestCandle.value || !previousCandle.value) return ''
  return latestCandle.value.close >= previousCandle.value.close ? 'positive' : 'negative'
})
const priceDirectionText = computed(() => {
  if (!latestCandle.value || !previousCandle.value) return '--'
  return latestCandle.value.close >= previousCandle.value.close ? 'Bullish' : 'Bearish'
})
const selectedIntervalLabel = computed(() => intervalOptions.find((item) => item.value === selectedInterval.value)?.label ?? selectedInterval.value)
const chartTypeLabel = computed(() => chartMode.value === 'candlestick' ? 'Candles' : 'Line')
const indicatorLabel = computed(() => indicatorMode.value.toUpperCase())

const topFactors = computed(() => factors.value?.feature_importance?.slice(0, 8) ?? [])

const macroHighlights = computed(() => {
  const items = history.value.slice(-4)
  if (items.length === 0) return []
  return [
    { label: 'Latest Close', value: formatPrice(items.at(-1)?.close) },
    { label: 'Avg Volume', value: formatVolume(avg(items.map((item) => item.volume))) },
    { label: '7-bar High', value: formatPrice(Math.max(...items.map((item) => item.high))) },
    { label: '7-bar Low', value: formatPrice(Math.min(...items.map((item) => item.low))) },
  ]
})

const sentimentHighlights = computed(() => {
  if (!factors.value?.feature_importance?.length) {
    return [
      { label: 'Top Factor', value: 'Loading...' },
      { label: 'SHAP', value: 'N/A' },
      { label: 'Causality', value: 'N/A' },
      { label: 'Correlation', value: 'N/A' },
    ]
  }
  return [
    { label: 'Top Factor', value: factors.value.feature_importance[0]?.feature ?? 'N/A' },
    { label: '2nd Factor', value: factors.value.feature_importance[1]?.feature ?? 'N/A' },
    { label: '3rd Factor', value: factors.value.feature_importance[2]?.feature ?? 'N/A' },
    { label: 'SHAP Rows', value: String(factors.value.shap_summary.length) },
  ]
})

function formatNumber(value?: number | null) {
  if (value === null || value === undefined || Number.isNaN(value)) return '--'
  return new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(value)
}

function formatVolume(value?: number | null) {
  if (value === null || value === undefined || Number.isNaN(value)) return '--'
  return new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 }).format(value)
}

function formatAmount(value?: number | null) {
  if (value === null || value === undefined || Number.isNaN(value)) return '--'
  return new Intl.NumberFormat('en-US', { maximumFractionDigits: 4 }).format(value)
}

function formatPrice(value?: number | null, decimals = priceDecimals.value) {
  if (value === null || value === undefined || Number.isNaN(value)) return '--'
  return `$${new Intl.NumberFormat('en-US', { maximumFractionDigits: decimals }).format(value)}`
}

function formatChange(value?: number | null) {
  if (value === null || value === undefined || Number.isNaN(value)) return '--'
  const sign = value > 0 ? '+' : ''
  return `${sign}${value.toFixed(2)}%`
}

function formatDateTime(value: string) {
  const date = new Date(value)
  return new Intl.DateTimeFormat('en-US', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(date)
}

function formatTradeTime(value: string) {
  const date = new Date(value)
  return new Intl.DateTimeFormat('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  }).format(date)
}

function avg(values: number[]) {
  if (!values.length) return 0
  return values.reduce((sum, value) => sum + value, 0) / values.length
}

function limitForInterval(interval: IntervalKey) {
  return intervalOptions.find((item) => item.value === interval)?.limit ?? 240
}

function calcMA(values: number[], period: number) {
  return values.map((_, index) => {
    if (index < period - 1) return '-'
    const slice = values.slice(index - period + 1, index + 1)
    return avg(slice).toFixed(2)
  })
}

function calcEMA(values: number[], period: number) {
  const k = 2 / (period + 1)
  const result: number[] = []
  let prev = values[0] ?? 0
  values.forEach((value, index) => {
    if (index === 0) {
      prev = value
      result.push(value)
      return
    }
    const ema = value * k + prev * (1 - k)
    result.push(ema)
    prev = ema
  })
  return result
}

function calcBoll(values: number[], period = 20) {
  return values.map((_, index) => {
    if (index < period - 1) return { upper: '-', mid: '-', lower: '-' }
    const slice = values.slice(index - period + 1, index + 1)
    const mid = avg(slice)
    const variance = avg(slice.map((value) => (value - mid) ** 2))
    const std = Math.sqrt(variance)
    return {
      upper: (mid + 2 * std).toFixed(2),
      mid: mid.toFixed(2),
      lower: (mid - 2 * std).toFixed(2),
    }
  })
}

function calcMACD(values: number[]) {
  const ema12 = calcEMA(values, 12)
  const ema26 = calcEMA(values, 26)
  const dif = values.map((_, index) => (ema12[index] ?? 0) - (ema26[index] ?? 0))
  const dea = calcEMA(dif, 9)
  const macd = dif.map((value, index) => (value - (dea[index] ?? 0)) * 2)
  return { dif, dea, macd }
}

function calcRSI(values: number[], period = 14) {
  const result: Array<number | '-'> = []
  result.push('-')
  let gains = 0
  let losses = 0
  for (let i = 1; i < values.length; i += 1) {
    const diff = values[i] - values[i - 1]
    if (diff >= 0) gains += diff
    else losses += Math.abs(diff)

    if (i < period) {
      result.push('-')
      continue
    }

    if (i > period) {
      const prevDiff = values[i - period + 1] - values[i - period]
      if (prevDiff >= 0) gains -= prevDiff
      else losses -= Math.abs(prevDiff)
    }

    const avgGain = gains / period
    const avgLoss = losses / period
    const rs = avgLoss === 0 ? 100 : avgGain / avgLoss
    const rsi = 100 - 100 / (1 + rs)
    result.push(Number.isFinite(rsi) ? Number(rsi.toFixed(2)) : '-')
  }
  while (result.length < values.length) result.unshift('-')
  return result
}

function formatXAxisLabel(value: string) {
  const date = new Date(value)
  if (selectedInterval.value === '1m' || selectedInterval.value === '5m' || selectedInterval.value === '15m' || selectedInterval.value === '1H' || selectedInterval.value === '4H') {
    return new Intl.DateTimeFormat('en-US', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    }).format(date)
  }
  return new Intl.DateTimeFormat('en-US', {
    month: '2-digit',
    day: '2-digit',
  }).format(date)
}

function renderTrendChart() {
  if (!trendEl.value || history.value.length === 0) return

  const closes = history.value.map((item) => item.close)
  const categories = history.value.map((item) => item.ts)
  const candleData = history.value.map((item) => [item.open, item.close, item.low, item.high])
  const volumeData = history.value.map((item) => ({
    value: item.volume,
    itemStyle: {
      color: item.close >= item.open ? '#00c087' : '#f6465d',
    },
  }))

  const ma5 = calcMA(closes, 5)
  const ma10 = calcMA(closes, 10)
  const ma20 = calcMA(closes, 20)
  const ma60 = calcMA(closes, 60)
  const boll = calcBoll(closes, 20)
  const macd = calcMACD(closes)
  const rsi = calcRSI(closes, 14)

  trendChart ??= echarts.init(trendEl.value)
  trendChart.setOption({
    backgroundColor: 'transparent',
    animation: false,
    legend: {
      top: 8,
      left: 8,
      textStyle: { color: '#9fb1cc' },
      data: ['Price', 'MA5', 'MA10', 'MA20', 'MA60', 'BOLL U', 'BOLL M', 'BOLL L', 'Volume', 'MACD', 'Signal', 'RSI'],
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      backgroundColor: 'rgba(8, 14, 26, 0.96)',
      borderColor: '#24304a',
      textStyle: { color: '#e8eefc' },
      formatter: (params: any[]) => {
        const idx = params?.[0]?.dataIndex ?? 0
        const row = history.value[idx]
        if (!row) return ''
        const pieces = [
          `<div style="margin-bottom:8px;font-weight:700">${formatXAxisLabel(row.ts)}</div>`,
          `<div>Open: ${formatPrice(row.open)}</div>`,
          `<div>High: ${formatPrice(row.high)}</div>`,
          `<div>Low: ${formatPrice(row.low)}</div>`,
          `<div>Close: ${formatPrice(row.close)}</div>`,
          `<div>Volume: ${formatVolume(row.volume)}</div>`,
        ]
        if (indicatorMode.value === 'macd') {
          pieces.push(`<div>MACD: ${(macd.macd[idx] ?? 0).toFixed(2)}</div>`, `<div>DIF: ${(macd.dif[idx] ?? 0).toFixed(2)}</div>`, `<div>DEA: ${(macd.dea[idx] ?? 0).toFixed(2)}</div>`)
        } else {
          pieces.push(`<div>RSI: ${(rsi[idx] ?? '-').toString()}</div>`)
        }
        return pieces.join('')
      },
    },
    axisPointer: {
      link: [{ xAxisIndex: [0, 1, 2] }],
      label: { backgroundColor: '#5b6b85' },
    },
    grid: [
      { left: 60, right: 28, top: 64, height: '48%' },
      { left: 60, right: 28, top: '66%', height: '14%' },
      { left: 60, right: 28, top: '82%', height: '12%' },
    ],
    xAxis: [
      {
        type: 'category',
        data: categories,
        boundaryGap: true,
        axisLine: { lineStyle: { color: '#30415f' } },
        axisLabel: {
          color: '#7e90aa',
          formatter: formatXAxisLabel,
        },
        axisTick: { show: false },
        splitLine: { show: false },
      },
      {
        type: 'category',
        gridIndex: 1,
        data: categories,
        boundaryGap: true,
        axisLine: { lineStyle: { color: '#30415f' } },
        axisLabel: { show: false },
        axisTick: { show: false },
        splitLine: { show: false },
      },
      {
        type: 'category',
        gridIndex: 2,
        data: categories,
        boundaryGap: true,
        axisLine: { lineStyle: { color: '#30415f' } },
        axisLabel: { show: false },
        axisTick: { show: false },
        splitLine: { show: false },
      },
    ],
    yAxis: [
      {
        scale: true,
        axisLine: { lineStyle: { color: '#30415f' } },
        axisLabel: { color: '#7e90aa' },
        splitLine: { lineStyle: { color: '#1a2437' } },
      },
      {
        scale: true,
        gridIndex: 1,
        axisLine: { lineStyle: { color: '#30415f' } },
        axisLabel: { color: '#7e90aa' },
        splitLine: { show: false },
      },
      {
        scale: true,
        gridIndex: 2,
        axisLine: { lineStyle: { color: '#30415f' } },
        axisLabel: { color: '#7e90aa' },
        splitLine: { lineStyle: { color: '#1a2437' } },
      },
    ],
    dataZoom: [
      { type: 'inside', xAxisIndex: [0, 1, 2], start: 40, end: 100 },
      { type: 'slider', xAxisIndex: [0, 1, 2], bottom: 8, height: 20, borderColor: '#24304a', backgroundColor: 'rgba(255,255,255,0.03)', textStyle: { color: '#7e90aa' } },
    ],
    series: [
      ...(chartMode.value === 'candlestick'
        ? [
            {
              name: 'Price',
              type: 'candlestick',
              data: candleData,
              itemStyle: {
                color: '#00c087',
                color0: '#f6465d',
                borderColor: '#00c087',
                borderColor0: '#f6465d',
              },
            },
          ]
        : [
            {
              name: 'Price',
              type: 'line',
              data: closes,
              smooth: true,
              showSymbol: false,
              lineStyle: { width: 2, color: '#56cfe1' },
              areaStyle: { color: 'rgba(86, 207, 225, 0.10)' },
            },
          ]),
      { name: 'MA5', type: 'line', data: ma5, showSymbol: false, smooth: true, lineStyle: { width: 1.5, color: '#f7b267' } },
      { name: 'MA10', type: 'line', data: ma10, showSymbol: false, smooth: true, lineStyle: { width: 1.5, color: '#ffd166' } },
      { name: 'MA20', type: 'line', data: ma20, showSymbol: false, smooth: true, lineStyle: { width: 1.5, color: '#9b5de5' } },
      { name: 'MA60', type: 'line', data: ma60, showSymbol: false, smooth: true, lineStyle: { width: 1.5, color: '#8d99ae' } },
      { name: 'BOLL U', type: 'line', data: boll.map((item) => item.upper), showSymbol: false, smooth: true, lineStyle: { width: 1, type: 'dashed', color: '#3aa0ff' } },
      { name: 'BOLL M', type: 'line', data: boll.map((item) => item.mid), showSymbol: false, smooth: true, lineStyle: { width: 1, type: 'dashed', color: '#3aa0ff' } },
      { name: 'BOLL L', type: 'line', data: boll.map((item) => item.lower), showSymbol: false, smooth: true, lineStyle: { width: 1, type: 'dashed', color: '#3aa0ff' } },
      {
        name: 'Volume',
        type: 'bar',
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: volumeData,
        barWidth: '60%',
      },
      {
        name: 'Volume MA',
        type: 'line',
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: calcMA(history.value.map((item) => item.volume), 20),
        showSymbol: false,
        smooth: true,
        lineStyle: { width: 1.2, color: '#56cfe1' },
      },
      ...(indicatorMode.value === 'macd'
        ? [
            {
              name: 'MACD',
              type: 'bar',
              xAxisIndex: 2,
              yAxisIndex: 2,
              data: macd.macd.map((value) => ({ value, itemStyle: { color: value >= 0 ? '#00c087' : '#f6465d' } })),
              barWidth: '60%',
            },
            {
              name: 'Signal',
              type: 'line',
              xAxisIndex: 2,
              yAxisIndex: 2,
              data: macd.dea,
              showSymbol: false,
              smooth: true,
              lineStyle: { width: 1.5, color: '#f7b267' },
            },
          ]
        : [
            {
              name: 'RSI',
              type: 'line',
              xAxisIndex: 2,
              yAxisIndex: 2,
              data: rsi,
              showSymbol: false,
              smooth: true,
              lineStyle: { width: 1.5, color: '#ff9f1c' },
            },
            {
              name: 'RSI 70',
              type: 'line',
              xAxisIndex: 2,
              yAxisIndex: 2,
              data: Array(history.value.length).fill(70),
              showSymbol: false,
              lineStyle: { width: 1, type: 'dashed', color: '#f6465d' },
            },
            {
              name: 'RSI 30',
              type: 'line',
              xAxisIndex: 2,
              yAxisIndex: 2,
              data: Array(history.value.length).fill(30),
              showSymbol: false,
              lineStyle: { width: 1, type: 'dashed', color: '#00c087' },
            },
          ]),
    ],
  })
}

async function loadOverview() {
  overview.value = await fetchOverview(selectedPair.value)
}

async function loadFactors() {
  const symbol = selectedPairSymbol.value
  factors.value = await fetchFactors(symbol, selectedPair.value)
}

async function loadMarketMeta() {
  instrument.value = await fetchInstrument(selectedPair.value)
  orderbook.value = await fetchOrderbook(selectedPair.value, 20)
  recentTrades.value = await fetchTrades(selectedPair.value, 20)
}

async function loadHistorySeries() {
  loadingHistory.value = true
  try {
    history.value = await fetchHistory(limitForInterval(selectedInterval.value), selectedInterval.value, selectedPair.value)
    renderTrendChart()
  } finally {
    loadingHistory.value = false
  }
}

async function runPrediction() {
  predicting.value = true
  try {
    prediction.value = await predict(modelName.value, horizonDays.value, selectedPairSymbol.value, selectedPair.value)
    ElMessage.success('Prediction updated')
  } catch (error) {
    ElMessage.error('Prediction request failed')
    console.error(error)
  } finally {
    predicting.value = false
  }
}

function resizeChart() {
  trendChart?.resize()
}

async function refreshLiveFeed() {
  await Promise.all([loadOverview(), loadMarketMeta()])
}

watch(selectedInterval, () => {
  loadHistorySeries()
})

watch([chartMode, indicatorMode], () => {
  renderTrendChart()
})

watch(selectedPair, async () => {
  await Promise.all([loadOverview(), loadFactors(), loadHistorySeries(), loadMarketMeta()])
  await runPrediction()
})

watch(history, () => {
  renderTrendChart()
}, { deep: true })

onMounted(async () => {
  await Promise.all([loadOverview(), loadFactors(), loadHistorySeries(), loadMarketMeta()])
  await runPrediction()
  window.addEventListener('resize', resizeChart)
  feedTimer = window.setInterval(() => {
    refreshLiveFeed().catch((error) => console.error('Live feed refresh failed', error))
  }, 15000)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeChart)
  trendChart?.dispose()
  if (feedTimer) window.clearInterval(feedTimer)
})
</script>

<style scoped>
.shell {
  min-height: 100vh;
  padding: 28px;
  color: #e8eefc;
  background:
    radial-gradient(circle at top left, rgba(0, 192, 135, 0.15), transparent 28%),
    radial-gradient(circle at top right, rgba(86, 207, 225, 0.12), transparent 24%),
    linear-gradient(180deg, #08111f 0%, #050814 100%);
}

.hero {
  display: grid;
  grid-template-columns: 1.6fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}

.hero-copy,
.hero-stats,
.panel {
  background: rgba(8, 14, 26, 0.78);
  border: 1px solid rgba(120, 145, 180, 0.18);
  border-radius: 22px;
  backdrop-filter: blur(18px);
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.28);
}

.hero-copy {
  padding: 24px;
}

.eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.26em;
  color: #7ad7ff;
  font-size: 12px;
  margin-bottom: 12px;
}

h1 {
  margin: 0;
  font-size: clamp(2.2rem, 4vw, 4.8rem);
  line-height: 1.02;
  max-width: 14ch;
}

p {
  max-width: 68ch;
  color: rgba(232, 238, 252, 0.74);
  line-height: 1.7;
}

.hero-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 18px;
}

.badge {
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(120, 145, 180, 0.18);
  color: #dbe7f6;
  font-size: 12px;
}

.hero-stats {
  display: grid;
  gap: 12px;
  padding: 18px;
}

.stat-card {
  padding: 18px;
  border-radius: 16px;
  background: linear-gradient(180deg, rgba(18, 26, 44, 0.96), rgba(12, 18, 32, 0.92));
  border: 1px solid rgba(120, 145, 180, 0.14);
}

.stat-card span,
.summary-chip span,
.snapshot-item span,
.metric-row span,
.mini-card span,
.rank-item span {
  display: block;
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(232, 238, 252, 0.54);
}

.stat-card strong {
  display: block;
  margin-top: 10px;
  font-size: 1.6rem;
}

.workspace {
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  gap: 20px;
}

.panel {
  padding: 20px;
}

.chart-panel {
  grid-column: span 8;
}

.side-panel {
  grid-column: span 4;
}

.panel-wide {
  grid-column: span 12;
}

.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 16px;
}

.panel-head h2,
.panel-head h3 {
  margin: 0;
}

.panel-head span,
.subline {
  color: rgba(232, 238, 252, 0.56);
  font-size: 0.9rem;
}

.chart-head {
  align-items: flex-start;
}

.chart-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: flex-end;
}

.pair-select {
  min-width: 150px;
}

.interval-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.interval-btn {
  border: 1px solid rgba(120, 145, 180, 0.18);
  background: rgba(255, 255, 255, 0.03);
  color: #dce7f5;
  border-radius: 10px;
  padding: 7px 11px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.interval-btn:hover,
.interval-btn.active {
  background: linear-gradient(180deg, rgba(0, 192, 135, 0.18), rgba(0, 192, 135, 0.06));
  border-color: rgba(0, 192, 135, 0.35);
  color: #ffffff;
}

.mode-group :deep(.el-radio-button__inner) {
  background: rgba(255, 255, 255, 0.03);
  border-color: rgba(120, 145, 180, 0.18);
  color: #dce7f5;
}

.mode-group :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: #00c087;
  border-color: #00c087;
  color: #04111f;
  box-shadow: none;
}

.chart-summary {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 14px;
}

.summary-chip {
  padding: 12px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(120, 145, 180, 0.12);
}

.summary-chip strong {
  display: block;
  margin-top: 8px;
  font-size: 1.02rem;
}

.trend-chart {
  width: 100%;
  height: 760px;
}

.snapshot-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.snapshot-item,
.metric-row {
  padding: 14px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(120, 145, 180, 0.12);
}

.snapshot-item strong,
.metric-row strong,
.mini-card strong,
.rank-item strong {
  display: block;
  margin-top: 8px;
  font-size: 1rem;
}

.mini-metrics {
  display: grid;
  gap: 10px;
  margin-top: 12px;
}

.orderbook-section,
.trade-section {
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid rgba(120, 145, 180, 0.14);
}

.orderbook-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.orderbook-column {
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.03);
  padding: 12px;
}

.orderbook-title {
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(232, 238, 252, 0.56);
  margin-bottom: 10px;
}

.orderbook-row {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 8px;
  padding: 6px 0;
  font-size: 13px;
}

.orderbook-row .price {
  font-variant-numeric: tabular-nums;
}

.orderbook-row .size {
  color: rgba(232, 238, 252, 0.68);
  font-variant-numeric: tabular-nums;
}

.orderbook-column.asks .price {
  color: #f6465d;
}

.orderbook-column.bids .price {
  color: #00c087;
}

.trade-list {
  display: grid;
  gap: 8px;
  max-height: 320px;
  overflow: auto;
}

.trade-row {
  display: grid;
  grid-template-columns: 84px 54px 1fr 1fr;
  gap: 10px;
  align-items: center;
  padding: 8px 10px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.03);
  font-size: 13px;
}

.trade-row.buy .price,
.trade-row.buy .side {
  color: #00c087;
}

.trade-row.sell .price,
.trade-row.sell .side {
  color: #f6465d;
}

.trade-row .time,
.trade-row .size {
  color: rgba(232, 238, 252, 0.7);
  font-variant-numeric: tabular-nums;
}

.trade-row .price,
.trade-row .side {
  font-variant-numeric: tabular-nums;
  font-weight: 600;
}

.panel-inner {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid rgba(120, 145, 180, 0.14);
}

.compact {
  margin-bottom: 12px;
}

.controls {
  display: grid;
  gap: 10px;
}

.control {
  width: 100%;
}

.predict-btn {
  width: 100%;
}

.prediction-box {
  margin-top: 14px;
  padding: 18px;
  border-radius: 16px;
  background: linear-gradient(180deg, rgba(46, 59, 92, 0.32), rgba(14, 19, 34, 0.72));
  border: 1px solid rgba(120, 145, 180, 0.18);
}

.prediction-price {
  font-size: 2rem;
  font-weight: 800;
  margin-bottom: 6px;
}

.prediction-meta {
  color: rgba(232, 238, 252, 0.68);
  margin-top: 4px;
}

.metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-top: 18px;
}

.metric-item {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  padding: 10px 12px;
}

.factor-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.factor-card {
  padding: 18px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(120, 145, 180, 0.12);
}

.rank-list {
  display: grid;
  gap: 10px;
  margin-top: 14px;
}

.rank-item {
  display: grid;
  grid-template-columns: 42px 1fr auto;
  gap: 10px;
  align-items: center;
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.03);
}

.two-col {
  grid-template-columns: 1fr 1fr;
}

.mini-grid {
  display: grid;
  gap: 10px;
  margin-top: 14px;
}

.mini-card {
  padding: 14px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.03);
}

.notes {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  margin-top: 18px;
}

.notes > div {
  padding: 16px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.03);
}

.notes p {
  margin-bottom: 0;
}

.positive {
  color: #00c087;
}

.negative {
  color: #f6465d;
}

@media (max-width: 1200px) {
  .hero,
  .workspace,
  .factor-grid {
    grid-template-columns: 1fr;
  }

  .chart-panel,
  .side-panel,
  .panel-wide {
    grid-column: span 1;
  }

  .chart-summary {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .shell {
    padding: 16px;
  }

  .trend-chart {
    height: 640px;
  }

  .chart-summary,
  .notes,
  .two-col,
  .snapshot-grid,
  .metrics {
    grid-template-columns: 1fr;
  }

  .chart-actions {
    justify-content: flex-start;
  }

  .orderbook-grid,
  .trade-row {
    grid-template-columns: 1fr;
  }
}
</style>
