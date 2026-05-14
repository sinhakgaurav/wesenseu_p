import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Download, TrendingUp, BedDouble, Ticket, CheckCircle, Loader2, RefreshCw } from 'lucide-react'
import {
  LineChart, Line, BarChart, Bar, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts'
import api from '@/lib/api'

const PERIOD_OPTIONS = [
  { label: '7 days', value: 7 },
  { label: '30 days', value: 30 },
  { label: '90 days', value: 90 },
]

export function ReportsPage() {
  const [days, setDays] = useState(30)

  const { data: occupancy, isLoading: oLoading } = useQuery({
    queryKey: ['reports-occupancy', days],
    queryFn: () => api.get(`/reports/occupancy?days=${days}`).then(r => r.data),
  })

  const { data: tasks, isLoading: tLoading } = useQuery({
    queryKey: ['reports-tasks', days],
    queryFn: () => api.get(`/reports/tasks?days=${days}`).then(r => r.data),
  })

  const { data: tickets, isLoading: tkLoading } = useQuery({
    queryKey: ['reports-tickets', days],
    queryFn: () => api.get(`/reports/tickets?days=${days}`).then(r => r.data),
  })

  const { data: depts = [], isLoading: dLoading } = useQuery<any[]>({
    queryKey: ['reports-depts', days],
    queryFn: () => api.get(`/reports/departments?days=${days}`).then(r => r.data),
  })

  const { data: inventory = [], isLoading: iLoading } = useQuery<any[]>({
    queryKey: ['reports-inventory', days],
    queryFn: () => api.get(`/reports/inventory-consumption?days=${days}`).then(r => r.data),
  })

  const { data: revenue = [], isLoading: rLoading } = useQuery<any[]>({
    queryKey: ['reports-revenue', days],
    queryFn: () => api.get(`/reports/revenue?days=${days}`).then(r => r.data),
  })

  const isLoading = oLoading || tLoading || tkLoading || dLoading || iLoading || rLoading

  // Compact chart data (every Nth point for readability)
  const step = Math.max(1, Math.floor((occupancy?.data?.length || 1) / 14))
  const occData = occupancy?.data?.filter((_: any, i: number) => i % step === 0) || []
  const taskData = tasks?.data?.filter((_: any, i: number) => i % step === 0) || []
  const ticketData = tickets?.data?.filter((_: any, i: number) => i % step === 0) || []
  const revData = revenue?.filter((_: any, i: number) => i % step === 0) || []

  const totalRevenue = revenue.reduce((s: number, r: any) => s + (r.orders_revenue || 0), 0)

  const exportCSV = () => {
    const rows = [['Date', 'Occupied', 'Vacant', 'Occupancy %']]
    occData.forEach((d: any) => rows.push([d.date, d.occupied, d.vacant, d.occupancy_rate]))
    const csv = rows.map(r => r.join(',')).join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url; a.download = `monitour-report-${days}d.csv`; a.click()
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Reports & Analytics</h1>
          <p className="text-gray-500 text-sm">Live operational insights from database</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex bg-white border border-gray-200 rounded-lg overflow-hidden">
            {PERIOD_OPTIONS.map(opt => (
              <button key={opt.value} onClick={() => setDays(opt.value)}
                className={`px-4 py-2 text-sm font-medium transition-colors ${days === opt.value ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-50'}`}>
                {opt.label}
              </button>
            ))}
          </div>
          <button onClick={exportCSV} className="btn-secondary flex items-center gap-2">
            <Download className="w-4 h-4" /> Export CSV
          </button>
        </div>
      </div>

      {isLoading && (
        <div className="flex items-center justify-center gap-2 text-blue-600 py-4 mb-4">
          <Loader2 className="w-5 h-5 animate-spin" />
          <span className="text-sm">Loading live data...</span>
        </div>
      )}

      {/* KPI Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {[
          { label: 'Avg Occupancy', value: `${occupancy?.avg_occupancy_rate ?? '—'}%`, icon: BedDouble, color: 'blue' },
          { label: 'Task Completion', value: tasks ? `${Math.round((tasks.total_completed / Math.max(1, tasks.total_completed + tasks.total_overdue)) * 100)}%` : '—', icon: CheckCircle, color: 'green' },
          { label: 'SLA Breach Rate', value: tickets ? `${tickets.sla_breach_rate}%` : '—', icon: Ticket, color: 'orange' },
          { label: `Revenue (${days}d)`, value: `₹${totalRevenue.toLocaleString()}`, icon: TrendingUp, color: 'purple' },
        ].map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="card">
            <div className="flex items-start gap-3">
              <div className={`w-10 h-10 bg-${color}-50 rounded-xl flex items-center justify-center flex-shrink-0`}>
                <Icon className={`w-5 h-5 text-${color}-600`} />
              </div>
              <div>
                <p className="text-xs text-gray-500">{label}</p>
                <p className="text-xl font-bold text-gray-900">{value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Occupancy Trend */}
        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-1">Room Occupancy Trend</h3>
          <p className="text-xs text-gray-400 mb-4">Avg rate: {occupancy?.avg_occupancy_rate ?? 0}%</p>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={occData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#94a3b8' }} tickFormatter={d => d.slice(5)} />
              <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} unit="%" domain={[0, 100]} />
              <Tooltip formatter={(v: any) => [`${v}%`, 'Occupancy']} />
              <Area type="monotone" dataKey="occupancy_rate" stroke="#3b82f6" fill="#dbeafe" name="Occupancy %" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Task Performance */}
        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-1">Task Performance</h3>
          <p className="text-xs text-gray-400 mb-4">Completed: {tasks?.total_completed ?? 0} | Overdue: {tasks?.total_overdue ?? 0}</p>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={taskData} barSize={12}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#94a3b8' }} tickFormatter={d => d.slice(5)} />
              <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} />
              <Tooltip />
              <Legend />
              <Bar dataKey="completed" fill="#22c55e" radius={[3, 3, 0, 0]} name="Completed" />
              <Bar dataKey="pending" fill="#f59e0b" radius={[3, 3, 0, 0]} name="Pending" />
              <Bar dataKey="overdue" fill="#ef4444" radius={[3, 3, 0, 0]} name="Overdue" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Ticket Trend */}
        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-1">Ticket Volume</h3>
          <p className="text-xs text-gray-400 mb-4">Opened: {tickets?.total_opened ?? 0} | Resolved: {tickets?.total_resolved ?? 0} | SLA breach: {tickets?.sla_breach_rate ?? 0}%</p>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={ticketData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#94a3b8' }} tickFormatter={d => d.slice(5)} />
              <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="opened" stroke="#3b82f6" strokeWidth={2} dot={false} name="Opened" />
              <Line type="monotone" dataKey="resolved" stroke="#22c55e" strokeWidth={2} dot={false} name="Resolved" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Revenue */}
        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-1">Order Revenue</h3>
          <p className="text-xs text-gray-400 mb-4">Total: ₹{totalRevenue.toLocaleString()} over {days} days</p>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={revData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#94a3b8' }} tickFormatter={d => d.slice(5)} />
              <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} />
              <Tooltip formatter={(v: any) => [`₹${v}`, 'Revenue']} />
              <Area type="monotone" dataKey="orders_revenue" stroke="#8b5cf6" fill="#ede9fe" name="Revenue ₹" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Department Performance */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-4">Department Performance</h3>
          {dLoading ? <div className="flex justify-center py-8"><Loader2 className="w-6 h-6 animate-spin text-blue-400" /></div> : (
            <div className="space-y-3">
              {depts.length === 0 ? <p className="text-sm text-gray-400 text-center py-4">No department data</p> : depts.map((d: any) => (
                <div key={d.department} className="flex items-center gap-3">
                  <div className="flex-1">
                    <div className="flex justify-between text-sm mb-1">
                      <span className="font-medium text-gray-700">{d.department}</span>
                      <span className="text-gray-500">{d.tasks_completed} tasks · {d.tickets_resolved} tickets</span>
                    </div>
                    <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div className="h-full bg-blue-500 rounded-full"
                        style={{ width: `${Math.min(100, d.tasks_completed * 5)}%` }} />
                    </div>
                  </div>
                  <span className="text-xs text-gray-400 w-16 text-right">{d.employee_count} staff</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Inventory Consumption */}
        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-4">Top Inventory Consumed</h3>
          {iLoading ? <div className="flex justify-center py-8"><Loader2 className="w-6 h-6 animate-spin text-blue-400" /></div> : (
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {inventory.length === 0 ? <p className="text-sm text-gray-400 text-center py-4">No consumption data</p> : inventory.map((item: any, i: number) => (
                <div key={i} className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
                  <div>
                    <p className="text-sm font-medium text-gray-800">{item.item_name}</p>
                    <p className="text-xs text-gray-400 capitalize">{item.category}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold text-gray-700">{item.consumed} {item.unit}</p>
                    <p className="text-xs text-gray-400">₹{item.cost.toLocaleString()}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
