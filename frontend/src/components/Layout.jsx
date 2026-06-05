import { NavLink, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import { FiActivity, FiAlertTriangle, FiCpu, FiGrid, FiShare2 } from 'react-icons/fi'

const navItems = [
  { path: '/', label: 'Dashboard', icon: FiGrid },
  { path: '/alerts', label: 'Alert Center', icon: FiAlertTriangle },
  { path: '/insights', label: 'AI Insights', icon: FiCpu },
  { path: '/network', label: 'Network View', icon: FiShare2 },
]

export default function Layout({ children }) {
  const location = useLocation()

  return (
    <div className="flex h-screen overflow-hidden">
      <aside className="w-64 bg-pipeline-darker border-r border-pipeline-border flex flex-col">
        <div className="p-6 border-b border-pipeline-border">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-pipeline-accent to-pipeline-neon-blue flex items-center justify-center">
              <FiActivity className="text-white text-xl" />
            </div>
            <div>
              <h1 className="text-sm font-bold text-white">PipeGuard AI</h1>
              <p className="text-xs text-gray-500">Leak Detection System</p>
            </div>
          </div>
        </div>

        <nav className="flex-1 p-4 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `nav-link ${isActive ? 'active' : ''}`
              }
            >
              <item.icon className="text-lg" />
              <span className="text-sm">{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="p-4 border-t border-pipeline-border">
          <div className="glass-panel p-3">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-pipeline-safe animate-pulse" />
              <span className="text-xs text-gray-400">System Online</span>
            </div>
            <p className="text-xs text-gray-500 mt-1">Last scan: 2 min ago</p>
          </div>
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto p-6">
        <motion.div
          key={location.pathname}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          {children}
        </motion.div>
      </main>
    </div>
  )
}
