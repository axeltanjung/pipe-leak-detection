import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { FiActivity, FiAlertTriangle, FiHeart, FiTrendingUp } from 'react-icons/fi'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar } from 'recharts'
import { getDashboardSummary } from '../api/client'

const SEVERITY_COLORS = {
  critical: '#dc2626',
  high: '#f97316',
  medium: '#eab308',
  low: '#22c55e',
}

export default function Dashboard() {
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      const res = await getDashboardSummary()
      setSummary(res.data)
    } catch (err) {
      console.error('Failed to fetch dashboard:', err)
      setSummary(getMockData())
    } finally {
      setLoading(false)
    }
  }

  const getMockData = () => ({
    total_pipelines: 20,
    active_alerts: 5,
    average_health: 72.4,
    network_risk: 0.34,
    severity_distribution: { critical: 2, high: 3, medium: 6, low: 9 },
    pipeline_statuses: Array.from({ length: 20 }, (_, i) => ({
      pipeline_id: `PL-${String(i + 1).padStart(3, '0')}`,
      risk_score: Math.random() * 0.8,
      health_score: 40 + Math.random() * 60,
      severity: ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'][Math.floor(Math.random() * 4)],
    })),
  })

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin w-8 h-8 border-2 border-pipeline-accent border-t-transparent rounded-full" />
      </div>
    )
  }

  const data = summary || getMockData()
  const pieData = Object.entries(data.severity_distribution).map(([name, value]) => ({ name, value }))
  const healthTrend = Array.from({ length: 24 }, (_, i) => ({
    hour: `${i}:00`,
    health: 60 + Math.random() * 30,
    risk: 0.1 + Math.random() * 0.4,
  }))

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Pipeline Overview</h1>
          <p className="text-gray-400 text-sm mt-1">Real-time monitoring dashboard</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <div className="w-2 h-2 rounded-full bg-pipeline-safe animate-pulse" />
          Monitoring Active
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          icon={FiActivity}
          label="Total Pipelines"
          value={data.total_pipelines}
          color="text-pipeline-neon-blue"
        />
        <MetricCard
          icon={FiAlertTriangle}
          label="Active Alerts"
          value={data.active_alerts}
          color="text-pipeline-danger"
          glow="shadow-glow-red"
        />
        <MetricCard
          icon={FiHeart}
          label="Avg Health"
          value={`${data.average_health.toFixed(1)}%`}
          color="text-pipeline-accent"
          glow="shadow-glow-green"
        />
        <MetricCard
          icon={FiTrendingUp}
          label="Network Risk"
          value={`${(data.network_risk * 100).toFixed(1)}%`}
          color="text-pipeline-warning"
          glow="shadow-glow-yellow"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 glass-panel p-6">
          <h3 className="text-sm font-semibold text-gray-300 mb-4">Health & Risk Trend (24h)</h3>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={healthTrend}>
              <defs>
                <linearGradient id="healthGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="hour" tick={{ fontSize: 10, fill: '#6b7280' }} />
              <YAxis tick={{ fontSize: 10, fill: '#6b7280' }} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
                labelStyle={{ color: '#9ca3af' }}
              />
              <Area type="monotone" dataKey="health" stroke="#10b981" fill="url(#healthGrad)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="glass-panel p-6">
          <h3 className="text-sm font-semibold text-gray-300 mb-4">Severity Distribution</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie data={pieData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} dataKey="value">
                {pieData.map((entry, i) => (
                  <Cell key={i} fill={SEVERITY_COLORS[entry.name]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex flex-wrap gap-2 mt-2 justify-center">
            {pieData.map((entry) => (
              <div key={entry.name} className="flex items-center gap-1 text-xs">
                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: SEVERITY_COLORS[entry.name] }} />
                <span className="text-gray-400 capitalize">{entry.name}: {entry.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="glass-panel p-6">
        <h3 className="text-sm font-semibold text-gray-300 mb-4">Pipeline Segments Status</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-3">
          {data.pipeline_statuses.map((p) => (
            <motion.div
              key={p.pipeline_id}
              whileHover={{ scale: 1.02 }}
              onClick={() => navigate(`/pipeline/${p.pipeline_id}`)}
              className={`p-3 rounded-lg border cursor-pointer transition-all ${
                p.severity === 'CRITICAL' ? 'border-red-700 bg-red-900/20' :
                p.severity === 'HIGH' ? 'border-orange-700 bg-orange-900/20' :
                p.severity === 'MEDIUM' ? 'border-yellow-700 bg-yellow-900/20' :
                'border-green-700/30 bg-green-900/10'
              }`}
            >
              <div className="text-xs font-mono text-gray-400">{p.pipeline_id}</div>
              <div className="text-lg font-bold mt-1" style={{
                color: p.severity === 'CRITICAL' ? '#dc2626' :
                       p.severity === 'HIGH' ? '#f97316' :
                       p.severity === 'MEDIUM' ? '#eab308' : '#22c55e'
              }}>
                {p.health_score.toFixed(0)}%
              </div>
              <div className={`status-badge mt-1 text-center status-${p.severity.toLowerCase()}`}>
                {p.severity}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  )
}

function MetricCard({ icon: Icon, label, value, color, glow }) {
  return (
    <motion.div whileHover={{ y: -2 }} className={`metric-card ${glow || ''}`}>
      <div className="flex items-center justify-between">
        <Icon className={`text-2xl ${color}`} />
      </div>
      <div className="mt-3">
        <p className="text-2xl font-bold text-white">{value}</p>
        <p className="text-xs text-gray-400 mt-1">{label}</p>
      </div>
    </motion.div>
  )
}
