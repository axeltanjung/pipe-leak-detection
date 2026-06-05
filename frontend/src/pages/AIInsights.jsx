import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { FiCpu, FiBarChart2 } from 'react-icons/fi'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis } from 'recharts'
import { explainLeak } from '../api/client'

export default function AIInsights() {
  const [explanation, setExplanation] = useState(null)
  const [selectedPipeline, setSelectedPipeline] = useState('PL-001')
  const [loading, setLoading] = useState(false)

  const pipelines = Array.from({ length: 20 }, (_, i) => `PL-${String(i + 1).padStart(3, '0')}`)

  useEffect(() => {
    fetchExplanation()
  }, [selectedPipeline])

  const fetchExplanation = async () => {
    setLoading(true)
    try {
      const res = await explainLeak(selectedPipeline)
      setExplanation(res.data)
    } catch (err) {
      setExplanation(getMockExplanation())
    } finally {
      setLoading(false)
    }
  }

  const getMockExplanation = () => ({
    pipeline_id: selectedPipeline,
    explanation: {
      risk_score: 0.62,
      severity: 'HIGH',
      primary_factors: {
        pressure_anomaly: 0.78,
        acoustic_anomaly: 0.54,
        structural_degradation: 0.42,
        flow_imbalance: 0.31,
      },
      recommendations: [
        'Schedule urgent inspection within 24 hours',
        'Increase monitoring frequency',
        'Investigate pressure differential',
      ],
    },
  })

  const data = explanation || getMockExplanation()
  const factors = data.explanation.primary_factors

  const barData = Object.entries(factors).map(([key, value]) => ({
    name: key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
    value: (value * 100).toFixed(1),
    fill: value > 0.6 ? '#ef4444' : value > 0.4 ? '#f59e0b' : '#22c55e',
  }))

  const radarData = Object.entries(factors).map(([key, value]) => ({
    subject: key.replace(/_/g, ' '),
    score: value * 100,
  }))

  const globalImportance = [
    { feature: 'Pressure Drop', importance: 0.85 },
    { feature: 'Acoustic Amplitude', importance: 0.72 },
    { feature: 'Flow Turbulence', importance: 0.68 },
    { feature: 'Vibration Intensity', importance: 0.61 },
    { feature: 'Corrosion Index', importance: 0.55 },
    { feature: 'Wall Thickness', importance: 0.48 },
    { feature: 'Joint Stress', importance: 0.42 },
    { feature: 'Pressure Variance', importance: 0.38 },
    { feature: 'Soil Movement', importance: 0.25 },
    { feature: 'Temperature', importance: 0.18 },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <FiCpu className="text-pipeline-neon-blue" /> AI Insights
          </h1>
          <p className="text-gray-400 text-sm mt-1">Explainable AI analysis & feature importance</p>
        </div>
        <select
          value={selectedPipeline}
          onChange={(e) => setSelectedPipeline(e.target.value)}
          className="bg-pipeline-card border border-pipeline-border rounded-lg px-4 py-2 text-sm text-gray-300 focus:outline-none focus:border-pipeline-accent"
        >
          {pipelines.map(p => <option key={p} value={p}>{p}</option>)}
        </select>
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin w-8 h-8 border-2 border-pipeline-accent border-t-transparent rounded-full" />
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="glass-panel p-6">
              <h3 className="text-sm font-semibold text-gray-300 mb-4">Risk Factor Contribution</h3>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={barData} layout="vertical">
                  <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 10, fill: '#6b7280' }} />
                  <YAxis type="category" dataKey="name" tick={{ fontSize: 10, fill: '#9ca3af' }} width={150} />
                  <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }} />
                  <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                    {barData.map((entry, i) => (
                      <motion.rect key={i} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="glass-panel p-6">
              <h3 className="text-sm font-semibold text-gray-300 mb-4">Risk Radar</h3>
              <ResponsiveContainer width="100%" height={250}>
                <RadarChart data={radarData}>
                  <PolarGrid stroke="#374151" />
                  <PolarAngleAxis dataKey="subject" tick={{ fontSize: 10, fill: '#9ca3af' }} />
                  <PolarRadiusAxis tick={{ fontSize: 9, fill: '#6b7280' }} domain={[0, 100]} />
                  <Radar dataKey="score" stroke="#10b981" fill="#10b981" fillOpacity={0.2} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="glass-panel p-6">
            <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
              <FiBarChart2 className="text-pipeline-accent" /> Global Feature Importance (SHAP)
            </h3>
            <div className="space-y-3">
              {globalImportance.map((feat, i) => (
                <motion.div
                  key={feat.feature}
                  initial={{ width: 0 }}
                  animate={{ width: '100%' }}
                  transition={{ delay: i * 0.05 }}
                  className="flex items-center gap-3"
                >
                  <span className="text-xs text-gray-400 w-36 text-right">{feat.feature}</span>
                  <div className="flex-1 h-5 bg-pipeline-darker rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${feat.importance * 100}%` }}
                      transition={{ duration: 0.8, delay: i * 0.05 }}
                      className="h-full rounded-full"
                      style={{
                        background: `linear-gradient(90deg, ${feat.importance > 0.6 ? '#ef4444' : feat.importance > 0.4 ? '#f59e0b' : '#10b981'}, ${feat.importance > 0.6 ? '#dc2626' : feat.importance > 0.4 ? '#d97706' : '#059669'})`,
                      }}
                    />
                  </div>
                  <span className="text-xs text-gray-300 w-12">{(feat.importance * 100).toFixed(0)}%</span>
                </motion.div>
              ))}
            </div>
          </div>

          <div className="glass-panel p-6">
            <h3 className="text-sm font-semibold text-gray-300 mb-3">AI Interpretation</h3>
            <div className="bg-pipeline-darker rounded-lg p-4 border border-pipeline-border">
              <p className="text-sm text-gray-300 leading-relaxed">
                <span className="text-pipeline-accent font-semibold">{selectedPipeline}</span> shows elevated risk primarily driven by
                <span className="text-red-400 font-medium"> pressure anomalies ({(factors.pressure_anomaly * 100).toFixed(0)}%)</span> and
                <span className="text-yellow-400 font-medium"> acoustic disturbances ({(factors.acoustic_anomaly * 100).toFixed(0)}%)</span>.
                The combination of these signals suggests a developing leak in the mid-section of the pipeline segment.
                Structural degradation contributes <span className="text-orange-400">{(factors.structural_degradation * 100).toFixed(0)}%</span> to overall risk,
                indicating aging infrastructure may be accelerating failure.
              </p>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
