import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import PipelineDetail from './pages/PipelineDetail'
import AIInsights from './pages/AIInsights'
import AlertCenter from './pages/AlertCenter'
import NetworkView from './pages/NetworkView'

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/pipeline/:id" element={<PipelineDetail />} />
          <Route path="/insights" element={<AIInsights />} />
          <Route path="/alerts" element={<AlertCenter />} />
          <Route path="/network" element={<NetworkView />} />
        </Routes>
      </Layout>
    </Router>
  )
}

export default App
