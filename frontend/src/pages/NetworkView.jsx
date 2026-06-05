import { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import { FiShare2 } from 'react-icons/fi'
import { getNetworkView } from '../api/client'

export default function NetworkView() {
  const [network, setNetwork] = useState(null)
  const [loading, setLoading] = useState(true)
  const [hoveredNode, setHoveredNode] = useState(null)
  const canvasRef = useRef(null)

  useEffect(() => {
    fetchNetwork()
  }, [])

  useEffect(() => {
    if (network) drawNetwork()
  }, [network, hoveredNode])

  const fetchNetwork = async () => {
    try {
      const res = await getNetworkView()
      setNetwork(res.data)
    } catch (err) {
      setNetwork(getMockNetwork())
    } finally {
      setLoading(false)
    }
  }

  const getMockNetwork = () => ({
    nodes: Array.from({ length: 20 }, (_, i) => ({
      id: `PL-${String(i + 1).padStart(3, '0')}`,
      risk_score: Math.random() * 0.8,
      health_score: 30 + Math.random() * 70,
      severity: ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'][Math.floor(Math.random() * 4)],
    })),
    edges: Array.from({ length: 25 }, (_, i) => ({
      source: `PL-${String(Math.floor(Math.random() * 20) + 1).padStart(3, '0')}`,
      target: `PL-${String(Math.floor(Math.random() * 20) + 1).padStart(3, '0')}`,
      stress: Math.random() * 0.8,
    })),
  })

  const getNodeColor = (severity) => {
    switch (severity) {
      case 'CRITICAL': return '#dc2626'
      case 'HIGH': return '#f97316'
      case 'MEDIUM': return '#eab308'
      default: return '#22c55e'
    }
  }

  const drawNetwork = () => {
    const canvas = canvasRef.current
    if (!canvas || !network) return

    const ctx = canvas.getContext('2d')
    const width = canvas.width = canvas.offsetWidth * 2
    const height = canvas.height = canvas.offsetHeight * 2
    ctx.scale(2, 2)

    const w = width / 2
    const h = height / 2

    ctx.fillStyle = '#0a0e1a'
    ctx.fillRect(0, 0, w, h)

    const nodePositions = {}
    const n = network.nodes.length
    const centerX = w / 2
    const centerY = h / 2
    const radius = Math.min(w, h) * 0.35

    network.nodes.forEach((node, i) => {
      const angle = (2 * Math.PI * i) / n - Math.PI / 2
      nodePositions[node.id] = {
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle),
      }
    })

    network.edges.forEach(edge => {
      const source = nodePositions[edge.source]
      const target = nodePositions[edge.target]
      if (!source || !target) return

      ctx.beginPath()
      ctx.moveTo(source.x, source.y)
      ctx.lineTo(target.x, target.y)
      ctx.strokeStyle = `rgba(${Math.floor(edge.stress * 255)}, ${Math.floor((1 - edge.stress) * 150)}, 100, 0.3)`
      ctx.lineWidth = 1 + edge.stress * 2
      ctx.stroke()
    })

    network.nodes.forEach(node => {
      const pos = nodePositions[node.id]
      const color = getNodeColor(node.severity)
      const isHovered = hoveredNode === node.id
      const nodeRadius = isHovered ? 18 : 12

      ctx.beginPath()
      ctx.arc(pos.x, pos.y, nodeRadius + 4, 0, 2 * Math.PI)
      ctx.fillStyle = color + '30'
      ctx.fill()

      ctx.beginPath()
      ctx.arc(pos.x, pos.y, nodeRadius, 0, 2 * Math.PI)
      ctx.fillStyle = color
      ctx.fill()
      ctx.strokeStyle = color
      ctx.lineWidth = 2
      ctx.stroke()

      ctx.fillStyle = '#ffffff'
      ctx.font = `${isHovered ? 'bold ' : ''}9px monospace`
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillText(node.id.replace('PL-', ''), pos.x, pos.y)
    })
  }

  const handleCanvasClick = (e) => {
    if (!network || !canvasRef.current) return
    const rect = canvasRef.current.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top

    const n = network.nodes.length
    const w = rect.width
    const h = rect.height
    const centerX = w / 2
    const centerY = h / 2
    const radius = Math.min(w, h) * 0.35

    for (let i = 0; i < n; i++) {
      const angle = (2 * Math.PI * i) / n - Math.PI / 2
      const nx = centerX + radius * Math.cos(angle)
      const ny = centerY + radius * Math.sin(angle)
      const dist = Math.sqrt((x - nx) ** 2 + (y - ny) ** 2)
      if (dist < 20) {
        setHoveredNode(network.nodes[i].id)
        return
      }
    }
    setHoveredNode(null)
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-3">
          <FiShare2 className="text-pipeline-neon-blue" /> Pipeline Network
        </h1>
        <p className="text-gray-400 text-sm mt-1">Graph-based pipeline topology with risk coloring</p>
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin w-8 h-8 border-2 border-pipeline-accent border-t-transparent rounded-full" />
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
          <div className="lg:col-span-3 glass-panel p-4">
            <canvas
              ref={canvasRef}
              onClick={handleCanvasClick}
              className="w-full h-[500px] rounded-lg cursor-crosshair"
            />
          </div>

          <div className="space-y-4">
            <div className="glass-panel p-4">
              <h3 className="text-sm font-semibold text-gray-300 mb-3">Legend</h3>
              <div className="space-y-2">
                {[['CRITICAL', '#dc2626'], ['HIGH', '#f97316'], ['MEDIUM', '#eab308'], ['LOW', '#22c55e']].map(([label, color]) => (
                  <div key={label} className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
                    <span className="text-xs text-gray-400">{label}</span>
                  </div>
                ))}
              </div>
            </div>

            {hoveredNode && network && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="glass-panel p-4"
              >
                <h3 className="text-sm font-semibold text-white mb-2">{hoveredNode}</h3>
                {(() => {
                  const node = network.nodes.find(n => n.id === hoveredNode)
                  if (!node) return null
                  return (
                    <div className="space-y-2">
                      <div className="flex justify-between text-xs">
                        <span className="text-gray-400">Risk Score</span>
                        <span className="text-white">{(node.risk_score * 100).toFixed(1)}%</span>
                      </div>
                      <div className="flex justify-between text-xs">
                        <span className="text-gray-400">Health</span>
                        <span className="text-white">{node.health_score.toFixed(0)}%</span>
                      </div>
                      <div className="flex justify-between text-xs">
                        <span className="text-gray-400">Severity</span>
                        <span className={`status-badge status-${node.severity.toLowerCase()}`}>{node.severity}</span>
                      </div>
                    </div>
                  )
                })()}
              </motion.div>
            )}

            <div className="glass-panel p-4">
              <h3 className="text-sm font-semibold text-gray-300 mb-2">Network Stats</h3>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-gray-400">Total Nodes</span>
                  <span className="text-white">{network?.nodes.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Connections</span>
                  <span className="text-white">{network?.edges.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Critical Nodes</span>
                  <span className="text-red-400">{network?.nodes.filter(n => n.severity === 'CRITICAL').length}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
