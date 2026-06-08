<template>
  <div class="shell">
    <header class="hero">
      <div>
        <div class="eyebrow">CryptoSight</div>
        <h1>Financial Big Data-Driven Crypto Analysis & Prediction</h1>
        <p>
          BTC market overview, macro factors, sentiment signals, and model comparison in one dark financial dashboard.
        </p>
      </div>
      <el-card class="status-card" shadow="never">
        <div class="status-grid">
          <div>
            <div class="status-label">Current BTC</div>
            <div class="status-value">{{ formatPrice(overview?.current_price) }}</div>
          </div>
          <div>
            <div class="status-label">24h Change</div>
            <div class="status-value" :class="changeClass">{{ formatChange(overview?.change_24h) }}</div>
          </div>
          <div>
            <div class="status-label">Volume</div>
            <div class="status-value">{{ formatNumber(overview?.volume_24h) }}</div>
          </div>
        </div>
      </el-card>
    </header>

    <main class="grid">
      <section class="panel panel-wide">
        <div class="panel-head">
          <h2>Price Trend</h2>
          <span>{{ overview?.as_of ?? 'Loading...' }}</span>
        </div>
        <div ref="trendEl" class="chart"></div>
      </section>

      <section class="panel">
        <div class="panel-head">
          <h2>Prediction Center</h2>
          <span>Live API</span>
        </div>
        <div class="controls">
          <el-select v-model="modelName" class="control" placeholder="Select model">
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
          <el-button type="primary" :loading="predicting" @click="runPrediction">Predict</el-button>
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
      </section>

      <section class="panel">
        <div class="panel-head">
          <h2>Feature Importance</h2>
          <span>Random Forest</span>
        </div>
        <div ref="featureEl" class="chart small-chart"></div>
      </section>

      <section class="panel">
        <div class="panel-head">
          <h2>Macro + Sentiment</h2>
          <span>Factor Snapshot</span>
        </div>
        <div class="mini-grid">
          <div class="mini-card" v-for="item in macroHighlights" :key="item.label">
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
          </div>
        </div>
        <div class="mini-grid sentiment-grid">
          <div class="mini-card" v-for="item in sentimentHighlights" :key="item.label">
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
          </div>
        </div>
      </section>

      <section class="panel panel-wide">
        <div class="panel-head">
          <h2>Research Notes</h2>
          <span>Thesis-ready outputs</span>
        </div>
        <el-alert
          title="Use the API outputs to export figures for the thesis: correlation heatmaps, feature ranking charts, and model comparison tables."
          type="info"
          :closable="false"
          show-icon
        />
        <div class="notes">
          <div>
            <strong>Research question</strong>
            <p>Which factors most strongly affect cryptocurrency prices, and does multi-source data improve prediction accuracy?</p>
          </div>
          <div>
            <strong>Suggested next step</strong>
            <p>Replace demo seeding with real Binance/FRED/sentiment collectors and persist model results back into MySQL.</p>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onBeforeUnmount, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { fetchFactors, fetchHistory, fetchOverview, predict } from './api'
import type { FactorPayload, HistoryPoint, MarketOverview, PredictionResponse } from './types'

const overview = ref<MarketOverview | null>(null)
const history = ref<HistoryPoint[]>([])
const factors = ref<FactorPayload | null>(null)
const prediction = ref<PredictionResponse | null>(null)
const modelName = ref('xgboost')
const horizonDays = ref(7)
const predicting = ref(false)

const trendEl = ref<HTMLDivElement | null>(null)
const featureEl = ref<HTMLDivElement | null>(null)
let trendChart: echarts.ECharts | null = null
let featureChart: echarts.ECharts | null = null

const changeClass = computed(() => {
  const change = overview.value?.change_24h ?? 0
  return change >= 0 ? 'positive' : 'negative'
})

const macroHighlights = computed(() => {
  const items = history.value.slice(-4)
  if (items.length === 0) return []
  return [
    { label: 'Latest Close', value: formatPrice(items.at(-1)?.close) },
    { label: '7D Avg Volume', value: formatNumber(avg(items.map((item) => item.volume))) },
    { label: '7D High', value: formatPrice(Math.max(...items.map((item) => item.high))) },
    { label: '7D Low', value: formatPrice(Math.min(...items.map((item) => item.low))) },
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

function formatPrice(value?: number | null) {
  if (value === null || value === undefined || Number.isNaN(value)) return '--'
  return `$${new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 }).format(value)}`
}

function formatChange(value?: number | null) {
  if (value === null || value === undefined || Number.isNaN(value)) return '--'
  const sign = value > 0 ? '+' : ''
  return `${sign}${value.toFixed(2)}%`
}

function avg(values: number[]) {
  if (!values.length) return 0
  return values.reduce((sum, value) => sum + value, 0) / values.length
}

function renderTrendChart() {
  if (!trendEl.value || history.value.length === 0) return
  trendChart ??= echarts.init(trendEl.value)
  trendChart.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis' },
    grid: { left: 48, right: 24, top: 40, bottom: 40 },
    xAxis: { type: 'category', data: history.value.map((item) => item.ts.slice(0, 10)), axisLine: { lineStyle: { color: '#3c4a63' } } },
    yAxis: { type: 'value', scale: true, axisLine: { lineStyle: { color: '#3c4a63' } }, splitLine: { lineStyle: { color: '#1b263b' } } },
    series: [
      {
        name: 'Close',
        type: 'line',
        smooth: true,
        showSymbol: false,
        data: history.value.map((item) => item.close),
        lineStyle: { width: 3, color: '#56cfe1' },
        areaStyle: { color: 'rgba(86, 207, 225, 0.12)' },
      },
      {
        name: 'MA 7',
        type: 'line',
        smooth: true,
        showSymbol: false,
        data: history.value.map((_, index, arr) => {
          const start = Math.max(0, index - 6)
          const slice = arr.slice(start, index + 1).map((item) => item.close)
          return avg(slice)
        }),
        lineStyle: { width: 2, color: '#f7b267' },
      },
    ],
  })
}

function renderFeatureChart() {
  if (!featureEl.value || !factors.value?.feature_importance?.length) return
  featureChart ??= echarts.init(featureEl.value)
  const top = factors.value.feature_importance.slice(0, 8).reverse()
  featureChart.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 110, right: 24, top: 20, bottom: 16 },
    xAxis: { type: 'value', axisLine: { lineStyle: { color: '#3c4a63' } }, splitLine: { lineStyle: { color: '#1b263b' } } },
    yAxis: { type: 'category', data: top.map((item) => item.feature), axisLine: { lineStyle: { color: '#3c4a63' } } },
    series: [
      {
        type: 'bar',
        data: top.map((item) => item.importance),
        barWidth: 14,
        itemStyle: { color: '#7c5cff' },
      },
    ],
  })
}

async function loadDashboard() {
  const [overviewData, historyData, factorsData] = await Promise.all([
    fetchOverview(),
    fetchHistory(120),
    fetchFactors(),
  ])
  overview.value = overviewData
  history.value = historyData
  factors.value = factorsData
  renderTrendChart()
  renderFeatureChart()
}

async function runPrediction() {
  predicting.value = true
  try {
    prediction.value = await predict(modelName.value, horizonDays.value)
    ElMessage.success('Prediction updated')
  } catch (error) {
    ElMessage.error('Prediction request failed')
    console.error(error)
  } finally {
    predicting.value = false
  }
}

onMounted(async () => {
  await loadDashboard()
  window.addEventListener('resize', handleResize)
  await runPrediction()
})

function handleResize() {
  trendChart?.resize()
  featureChart?.resize()
}

watch([history, factors], () => {
  renderTrendChart()
  renderFeatureChart()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  trendChart?.dispose()
  featureChart?.dispose()
})
</script>

<style scoped>
.shell {
  min-height: 100vh;
  padding: 32px;
  color: #e8eefc;
}

.hero {
  display: grid;
  grid-template-columns: 1.5fr 1fr;
  gap: 24px;
  margin-bottom: 24px;
  align-items: stretch;
}

.eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.24em;
  color: #7ad7ff;
  font-size: 12px;
  margin-bottom: 12px;
}

h1 {
  margin: 0;
  font-size: clamp(2.2rem, 4vw, 4.6rem);
  line-height: 1.02;
  max-width: 12ch;
}

p {
  max-width: 62ch;
  color: rgba(232, 238, 252, 0.76);
  line-height: 1.7;
}

.status-card,
.panel {
  background: rgba(8, 14, 26, 0.7);
  border: 1px solid rgba(120, 145, 180, 0.2);
  border-radius: 20px;
  backdrop-filter: blur(18px);
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.28);
}

.status-card :deep(.el-card__body) {
  padding: 24px;
}

.status-grid {
  display: grid;
  gap: 18px;
}

.status-label {
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(232, 238, 252, 0.56);
}

.status-value {
  margin-top: 8px;
  font-size: 1.6rem;
  font-weight: 700;
}

.positive { color: #42d392; }
.negative { color: #ff6b6b; }

.grid {
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  gap: 24px;
}

.panel {
  padding: 20px;
  grid-column: span 6;
}

.panel-wide {
  grid-column: span 12;
}

.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 14px;
}

.panel-head h2 {
  margin: 0;
  font-size: 1.1rem;
}

.panel-head span {
  color: rgba(232, 238, 252, 0.56);
  font-size: 0.9rem;
}

.chart {
  width: 100%;
  height: 420px;
}

.small-chart {
  height: 320px;
}

.controls {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 18px;
}

.control {
  min-width: 150px;
  flex: 1;
}

.prediction-box {
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

.mini-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 16px;
}

.mini-card {
  padding: 14px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.04);
}

.mini-card span {
  display: block;
  font-size: 12px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: rgba(232, 238, 252, 0.56);
}

.mini-card strong {
  display: block;
  margin-top: 8px;
  font-size: 1.05rem;
}

.notes {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  margin-top: 18px;
}

.notes div {
  padding: 16px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.03);
}

.notes p {
  margin-bottom: 0;
}

@media (max-width: 1024px) {
  .hero {
    grid-template-columns: 1fr;
  }

  .panel {
    grid-column: span 12;
  }
}

@media (max-width: 768px) {
  .shell {
    padding: 16px;
  }

  .metrics,
  .mini-grid,
  .notes {
    grid-template-columns: 1fr;
  }

  .chart {
    height: 320px;
  }
}
</style>
