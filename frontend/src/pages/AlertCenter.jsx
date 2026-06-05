import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { FiAlertTriangle, FiCheckCircle, FiClock } from 'react-icons/fi'
import { getAlerts } from '../api/client'

export default function AlertCenter() {
  const [alerts, setAlerts] = useState([])
  const [filter, setFilter] = useState('ALL')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchAlerts()
  }, [])

  const fetchAlerts = async () => {
    try {
      const res = await getAlerts()
      setAlerts(res.data)
    } catch (err) {
      setAlerts(getMockAlerts())
    } finally {
      setLoading(false)
    }
  }

  const getMockAlerts = () => [
    { pipeline_id: 'PL-003', severity: 'CRITICAL', risk_score: 0.92, health_score: 8, recommendations: ['IMMEDIATE: Isolate pipeline', 'Deploy emergency response team', 'Reduce pressure to minimum'] },
    { pipeline_id: 'PL-007', severity: 'CRITICAL', risk_score: 0.87, health_score: 13, recommendations: ['Urgent inspection required', 'Monitor acoustic signals continuously'] },
    { pipeline_id: 'PL-012', severity: 'HIGH', risk_score: 0.73, health_score: 27, recommendations: ['Schedule inspection within 24h', 'Increase monitoring frequency'] },
    { pipeline_id: 'PL-015', severity: 'HIGH', risk_score: 0.68, health_score: 32, recommendations: ['Investigate pressure anomaly', 'Check flow meters'] },
    { pipeline_id: 'PL-019', severity: 'HIGH', risk_score: 0.62, health_score: 38, recommendations: ['Monitor structural integrity', 'Schedule PIG run'] },
    { pipeline_id: 'PL-002', severity: 'MEDIUM', risk_score: 0.45, health_score: 55, recommendations: ['Continue routine monitoring'] },
    { pipeline_id: 'PL-009', severity: 'MEDIUM', risk_score: 0.42, health_score: 58, recommendations: ['Review historical trends'] },
  ]

  const filteredAlerts = filter === 'ALL' ? alerts : alerts.filter(a => a.severity === filter)

  const severityIcon = (severity) => {
    switch (severity) {
      case 'CRITICAL': return <FiAlertTriangle className="text-red-400 text-xl" />
      case 'HIGH': return <FiAlertTriangle className="text-orange-400 text-xl" />
      default: return <FiClock className="text-yellow-400 text-xl" />
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <FiAlertTriangle className="text-red-400" /> Alert Center
          </h1>
          <p className="text-gray-400 text-sm mt-1">Active leak warnings and pipeline alerts</p>
        </div>
        <div className="flex gap-2">
          {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM'].map(s => (
            <button
              key={s}
              onClick={() => setFilter(s)}
              className={`px-3 py-1.5 text-xs rounded-lg border transition ${
                filter === s
                  ? 'border-pipeline-accent bg-pipeline-accent/20 text-pipeline-accent'
                  : 'border-pipeline-border text-gray-400 hover:text-white'
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <SummaryCard label="Critical" count={alerts.filter(a => a.severity === 'CRITICAL').length} color="text-red-400" bg="bg-red-900/20 border-red-800" />
        <SummaryCard label="High" count={alerts.filter(a => a.severity === 'HIGH').length} color="text-orange-400" bg="bg-orange-900/20 border-orange-800" />
        <SummaryCard label="Medium" count={alerts.filter(a => a.severity === 'MEDIUM').length} color="text-yellow-400" bg="bg-yellow-900/20 border-yellow-800" />
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin w-8 h-8 border-2 border-pipeline-accent border-t-transparent rounded-full" />
        </div>
      ) : (
        <div className="space-y-3">
          {filteredAlerts.map((alert, i) => (
            <motion.div
              key={`${alert.pipeline_id}-${i}`}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05 }}
              className={`glass-panel p-5 border-l-4 ${
                alert.severity === 'CRITICAL' ? 'border-l-red-500' :
                alert.severity === 'HIGH' ? 'border-l-orange-500' : 'border-l-yellow-500'
              }`}
            >
              <div className="flex items-start gap-4">
                {severityIcon(alert.severity)}
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span className="font-mono text-sm text-white">{alert.pipeline_id}</span>
                      <span className={`status-badge status-${alert.severity.toLowerCase()}`}>
                        {alert.severity}
                      </span>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-bold text-white">{(alert.risk_score * 100).toFixed(0)}% risk</p>
                      <p className="text-xs text-gray-500">Health: {alert.health_score.toFixed(0)}%</p>
                    </div>
                  </div>
                  <div className="mt-3 space-y-1">
                    {alert.recommendations.map((rec, j) => (
                      <p key={j} className="text-xs text-gray-400 flex items-center gap-2">
                        <span className="text-pipeline-accent">→</span> {rec}
                      </p>
                    ))}
                  </div>
                </div>
              </div>
            </motion.div>
          ))}

          {filteredAlerts.length === 0 && (
            <div className="glass-panel p-12 text-center">
              <FiCheckCircle className="text-4xl text-pipeline-accent mx-auto mb-3" />
              <p className="text-gray-400">No alerts matching current filter</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function SummaryCard({ label, count, color, bg }) {
  return (
    <div className={`rounded-xl border p-4 ${bg}`}>
      <p className="text-xs text-gray-400">{label} Alerts</p>
      <p className={`text-3xl font-bold mt-1 ${color}`}>{count}</p>
    </div>
  )
}
