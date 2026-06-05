import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const getDashboardSummary = () => api.get('/dashboard/summary')
export const getPipelineDetail = (id, nPoints = 500) => api.get(`/pipeline/${id}?n_points=${nPoints}`)
export const detectChangepoints = (id) => api.get(`/changepoint/detect/${id}`)
export const getAcousticAnomaly = (id) => api.get(`/anomaly/acoustic/${id}`)
export const getPressureAnomaly = (id) => api.get(`/anomaly/pressure/${id}`)
export const explainLeak = (id) => api.get(`/explain/leak/${id}`)
export const getAlerts = (severity) => api.get('/alerts', { params: { severity } })
export const getNetworkView = () => api.get('/network/view')
export const predictLeak = (features) => api.post('/predict/leak', features)
export const getHealth = () => api.get('/health')

export default api
