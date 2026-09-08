import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  r => r,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export const authApi = {
  login: (data) => api.post('/auth/token', new URLSearchParams(data)),
  me: () => api.get('/auth/me'),
  register: (data) => api.post('/auth/register', data),
  users: () => api.get('/auth/users'),
}

export const productsApi = {
  list: (type) => api.get('/bom/products', { params: { product_type: type } }),
  create: (data) => api.post('/bom/products', data),
  update: (id, data) => api.put(`/bom/products/${id}`, data),
  delete: (id) => api.delete(`/bom/products/${id}`),
  getBom: (id) => api.get(`/bom/products/${id}/bom`),
  getTree: (id) => api.get(`/bom/products/${id}/tree`),
  addBomItem: (data) => api.post('/bom/bom-items', data),
  deleteBomItem: (id) => api.delete(`/bom/bom-items/${id}`),
}

export const ordersApi = {
  list: (params) => api.get('/orders', { params }),
  create: (data) => api.post('/orders', data),
  update: (id, data) => api.put(`/orders/${id}`, data),
  delete: (id) => api.delete(`/orders/${id}`),
  import: (file) => {
    const fd = new FormData()
    fd.append('file', file)
    return api.post('/orders/import', fd)
  },
}

export const inventoryApi = {
  list: () => api.get('/inventory'),
  upsert: (data) => api.post('/inventory', data),
  update: (id, data) => api.put(`/inventory/${id}`, data),
  import: (file) => {
    const fd = new FormData()
    fd.append('file', file)
    return api.post('/inventory/import', fd)
  },
}

export const productionApi = {
  listLines: () => api.get('/production/lines'),
  createLine: (data) => api.post('/production/lines', data),
  updateLine: (id, data) => api.put(`/production/lines/${id}`, data),
  lineProducts: (id) => api.get(`/production/lines/${id}/products`),
  addLineProduct: (data) => api.post('/production/line-products', data),
  deleteLineProduct: (id) => api.delete(`/production/line-products/${id}`),
  getCalendar: (id, params) => api.get(`/production/lines/${id}/calendar`, { params }),
  addCalendar: (data) => api.post('/production/calendar', data),
  generateCalendar: (id, params) => api.post(`/production/lines/${id}/calendar/generate`, null, { params }),
  listChangeovers: (id) => api.get(`/production/lines/${id}/changeovers`),
  addChangeover: (data) => api.post('/production/changeovers', data),
  deleteChangeover: (id) => api.delete(`/production/changeovers/${id}`),
}

export const planningApi = {
  runMrp: () => api.post('/planning/mrp/calculate'),
  getNetRequirements: () => api.get('/planning/mrp/net-requirements'),
  runRccp: (params) => api.post('/planning/rccp/calculate', null, { params }),
  getRccpResults: () => api.get('/planning/rccp/results'),
  adjustRccp: (id, hours) => api.put(`/planning/rccp/${id}/adjust`, null, { params: { adjustment_hours: hours } }),
}

export const schedulingApi = {
  run: (params) => api.post('/scheduling/run', null, { params }),
  list: () => api.get('/scheduling/schedules'),
  get: (id) => api.get(`/scheduling/schedules/${id}`),
  approve: (id) => api.post(`/scheduling/schedules/${id}/approve`),
  compare: (ids) => api.post('/scheduling/compare', ids),
  simulate: (algorithm) => api.get(`/scheduling/simulation/${algorithm}`),
}

export const exportApi = {
  startVideoReport: (scheduleId) =>
    api.post('/export/video-report/jobs', null, {
      params: scheduleId != null ? { schedule_id: scheduleId } : {},
    }),
  videoReportStatus: (jobId) => api.get(`/export/video-report/jobs/${jobId}`),
  videoReportDownloadUrl: (jobId) => `/api/export/video-report/jobs/${jobId}/download`,
}

export const reportsApi = {
  dashboard: () => api.get('/reports/dashboard'),
  inventoryHealth: () => api.get('/reports/inventory-health'),
  orderFulfillment: () => api.get('/reports/order-fulfillment'),
  capacityUtilization: () => api.get('/reports/capacity-utilization'),
  wipAnalysis: () => api.get('/reports/wip-analysis'),
}

export default api
