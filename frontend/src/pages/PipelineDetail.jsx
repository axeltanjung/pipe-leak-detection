import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { FiArrowLeft, FiAlertCircle } from 'react-icons/fi'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine, AreaChart, Area } from 'recharts'
import { getPipelineDetail, detectChangepoints } from '../api/client'

export default function PipelineDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [detail, setDetail] = useState(null)
  const [changepoints, setChangepoints] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchData()
  }, [id])

  const fetchData = async () => {
    try {
      const [detailRes, cpRes] = await Promise.allSettled([
        getPipelineDetail(id),
        detectChangepoints(id),
      ])
      if (detailRes.status === 'fulfilled') setDetail(detailRes.value.data)
      if (cpRes.status === 'fulfilled') setChangepoints(cpRes.value.data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin w-8 h-8 border-2 border-pipeline-accent border-t-transparent rounded-full" />
      </div>
    )
  }

  const mockDetail = {
    pipeline_id: id,
    risk_assessment: { risk_score: 0.45, health_score: 55, severity: 'MEDIUM', recommendations: ['Monitor closely', 'Schedule inspection'] },
    time_series: {
      timestamps: Array.from({ length: 100 }, (_, i) => `2024-01-${String(Math.floor(i/4)+1).padStart(2,'0')} ${(i%4)*6}:00`),
      inlet_pressure: Array.from({ length: 100 }, () => 1200 + Math.random() * 100 - 50),
      outlet_pressure: Array.from({ length: 100 }, () => 1100 + Math.random() * 80 - 40),
      pressure_drop: Array.from({ length: 100 }, () => 80 + Math.random() * 40),
      flow_rate: Array.from({ length: 100 }, () => 2500 + Math.random() * 200 - 100),
      acoustic_signal_amplitude: Array.from({ length: 100 }, () => 20 + Math.random() * 15),
      vibration_intensity: Array.from({ length: 100 }, () => 5 + Math.random() * 8),
      leak_probability: Array.from({ length: 100 }, (_, i) => 0.1 + (i/100) * 0.5 + Math.random() * 0.1),
    },
    statistics: { avg_pressure: 1180, avg_flow: 2480, avg_acoustic: 28, pipe_age: 18 },
  }

  const d = detail || mockDetail
  const risk = d.risk_assessment

  const pressureData = d.time_series.timestamps.slice(-100).map((t, i) => ({
    time: t.split(' ')[1] || t,
    inlet: d.time_series.inlet_pressure[i],
    outlet: d.time_series.outlet_pressure[i],
    drop: d.time_series.pressure_drop[i],
  }))

  const flowData = d.time_series.timestamps.slice(-100).map((t, i) => ({
    time: t.split(' ')[1] || t,
    flow: d.time_series.flow_rate[i],
  }))

  const acousticData = d.time_series.timestamps.slice(-100).map((t, i) => ({
    time: t.split(' ')[1] || t,
    amplitude: d.time_series.acoustic_signal_amplitude[i],
    vibration: d.time_series.vibration_intensity[i],
  }))

  const leakProbData = d.time_series.timestamps.slice(-100).map((t, i) => ({
    time: t.split(' ')[1] || t,
    probability: d.time_series.leak_probability[i],
  }))

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <button onClick={() => navigate('/')} className="p-2 rounded-lg bg-pipeline-card hover:bg-pipeline-border transition">
          <FiArrowLeft />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-white">{d.pipeline_id}</h1>
          <p className="text-sm text-gray-400">Pipeline Segment Detail</p>
        </div>
        <div className={`ml-auto status-badge status-${risk.severity.toLowerCase()}`}>
          {risk.severity}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard label="Risk Score" value={`${(risk.risk_score * 100).toFixed(1)}%`} color={risk.risk_score > 0.5 ? 'text-red-400' : 'text-yellow-400'} />
        <StatCard label="Health Score" value={`${risk.health_score.toFixed(0)}%`} color={risk.health_score > 70 ? 'text-green-400' : 'text-yellow-400'} />
        <StatCard label="Avg Pressure" value={`${d.statistics.avg_pressure.toFixed(0)} psi`} color="text-blue-400" />
        <StatCard label="Pipe Age" value={`${d.statistics.pipe_age.toFixed(1)} yrs`} color="text-purple-400" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="glass-panel p-6">
          <h3 className="text-sm font-semibold text-gray-300 mb-4">Pressure Trends</h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={pressureData}>
              <XAxis dataKey="time" tick={{ fontSize: 9, fill: '#6b7280' }} interval={20} />
              <YAxis tick={{ fontSize: 10, fill: '#6b7280' }} />
              <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }} />
              <Line type="monotone" dataKey="inlet" stroke="#3b82f6" dot={false} strokeWidth={2} />
              <Line type="monotone" dataKey="outlet" stroke="#8b5cf6" dot={false} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="glass-panel p-6">
          <h3 className="text-sm font-semibold text-gray-300 mb-4">Flow Rate</h3>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={flowData}>
              <defs>
                <linearGradient id="flowGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#06b6d4" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="time" tick={{ fontSize: 9, fill: '#6b7280' }} interval={20} />
              <YAxis tick={{ fontSize: 10, fill: '#6b7280' }} />
              <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }} />
              <Area type="monotone" dataKey="flow" stroke="#06b6d4" fill="url(#flowGrad)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="glass-panel p-6">
          <h3 className="text-sm font-semibold text-gray-300 mb-4">Acoustic & Vibration Signals</h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={acousticData}>
              <XAxis dataKey="time" tick={{ fontSize: 9, fill: '#6b7280' }} interval={20} />
              <YAxis tick={{ fontSize: 10, fill: '#6b7280' }} />
              <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }} />
              <Line type="monotone" dataKey="amplitude" stroke="#f59e0b" dot={false} strokeWidth={2} />
              <Line type="monotone" dataKey="vibration" stroke="#ef4444" dot={false} strokeWidth={1.5} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="glass-panel p-6">
          <h3 className="text-sm font-semibold text-gray-300 mb-4">Leak Probability Timeline</h3>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={leakProbData}>
              <defs>
                <linearGradient id="leakGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="time" tick={{ fontSize: 9, fill: '#6b7280' }} interval={20} />
              <YAxis tick={{ fontSize: 10, fill: '#6b7280' }} domain={[0, 1]} />
              <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }} />
              <ReferenceLine y={0.5} stroke="#ef4444" strokeDasharray="3 3" />
              <Area type="monotone" dataKey="probability" stroke="#ef4444" fill="url(#leakGrad)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {risk.recommendations && (
        <div className="glass-panel p-6">
          <h3 className="text-sm font-semibold text-gray-300 mb-3 flex items-center gap-2">
            <FiAlertCircle className="text-yellow-400" /> Recommendations
          </h3>
          <ul className="space-y-2">
            {risk.recommendations.map((rec, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-gray-300">
                <span className="text-pipeline-accent mt-1">•</span>
                {rec}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

function StatCard({ label, value, color }) {
  return (
    <div className="glass-panel p-4">
      <p className="text-xs text-gray-500">{label}</p>
      <p className={`text-xl font-bold mt-1 ${color}`}>{value}</p>
    </div>
  )
}
