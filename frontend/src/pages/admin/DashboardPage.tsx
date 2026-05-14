import { useQuery } from '@tanstack/react-query'
import {
  BedDouble, ClipboardList, Ticket, Users,
  Package, Camera, TrendingUp, AlertTriangle,
  CheckCircle, Clock, ArrowUpRight
} from 'lucide-react'
import {
  PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid
} from 'recharts'
import api from '@/lib/api'
import type { DashboardStats } from '@/lib/types'
import { StatCard } from '@/components/ui/StatCard'
import { PageLoader } from '@/components/ui/LoadingSpinner'
import { useSelector } from 'react-redux'
import type { RootState } from '@/store'

const ROOM_COLORS = ['#3b82f6', '#22c55e', '#f59e0b', '#f97316', '#ef4444', '#a855f7', '#6b7280']

export function DashboardPage() {
  const user = useSelector((state: RootState) => state.auth.user)

  const { data: stats, isLoading } = useQuery<DashboardStats>({
    queryKey: ['dashboard', user?.property_id],
    queryFn: async () => {
      const params = user?.property_id ? `?property_id=${user.property_id}` : ''
      const { data } = await api.get(`/dashboard/stats${params}`)
      return data
    },
    refetchInterval: 30000,
  })

  if (isLoading) return <PageLoader />

  const taskChartData = stats ? [
    { name: 'Active', value: stats.active_tasks, color: '#3b82f6' },
    { name: 'Pending', value: stats.pending_tasks, color: '#f59e0b' },
    { name: 'Completed Today', value: stats.completed_tasks_today, color: '#22c55e' },
    { name: 'Overdue', value: stats.overdue_tasks, color: '#ef4444' },
  ] : []

  return (
    <div className="space-y-6">
      {/* Welcome */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Operations Dashboard</h1>
          <p className="text-gray-500 text-sm mt-0.5">
            {new Date().toLocaleDateString('en-IN', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
          </p>
        </div>
        <div className="flex items-center gap-2 bg-green-50 border border-green-200 rounded-lg px-3 py-2">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
          <span className="text-sm text-green-700 font-medium">Live</span>
        </div>
      </div>

      {/* Room stats */}
      <div>
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">Room Status</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <StatCard title="Total Rooms" value={stats?.total_rooms ?? 0} icon={BedDouble} iconBg="bg-blue-50" iconColor="text-blue-600" />
          <StatCard title="Occupied" value={stats?.occupied_rooms ?? 0} icon={BedDouble} iconBg="bg-indigo-50" iconColor="text-indigo-600" />
          <StatCard title="Vacant" value={stats?.vacant_rooms ?? 0} icon={CheckCircle} iconBg="bg-green-50" iconColor="text-green-600" />
          <StatCard title="Needs Cleaning" value={stats?.cleaning_pending ?? 0} icon={Clock} iconBg="bg-yellow-50" iconColor="text-yellow-600" />
          <StatCard title="Ready" value={stats?.ready_rooms ?? 0} icon={CheckCircle} iconBg="bg-emerald-50" iconColor="text-emerald-600" />
          <StatCard title="Maintenance" value={stats?.maintenance_rooms ?? 0} icon={AlertTriangle} iconBg="bg-red-50" iconColor="text-red-600" />
        </div>
      </div>

      {/* Operations stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          title="Active Tasks"
          value={stats?.active_tasks ?? 0}
          icon={ClipboardList}
          iconBg="bg-blue-50"
          iconColor="text-blue-600"
          subtitle={`${stats?.pending_tasks ?? 0} pending`}
        />
        <StatCard
          title="Open Tickets"
          value={stats?.open_tickets ?? 0}
          icon={Ticket}
          iconBg="bg-orange-50"
          iconColor="text-orange-600"
          subtitle={`${stats?.critical_tickets ?? 0} critical`}
        />
        <StatCard
          title="Available Staff"
          value={stats?.available_employees ?? 0}
          icon={Users}
          iconBg="bg-purple-50"
          iconColor="text-purple-600"
          subtitle={`of ${stats?.total_employees ?? 0} total`}
        />
        <StatCard
          title="Inventory Alerts"
          value={stats?.inventory_alerts ?? 0}
          icon={Package}
          iconBg="bg-red-50"
          iconColor="text-red-600"
          subtitle="Low stock items"
        />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Room status pie chart */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-900">Room Distribution</h3>
            <BedDouble className="w-5 h-5 text-gray-400" />
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie
                data={stats?.room_status_chart ?? []}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={90}
                dataKey="count"
                nameKey="label"
              >
                {(stats?.room_status_chart ?? []).map((_, index) => (
                  <Cell key={index} fill={ROOM_COLORS[index % ROOM_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(value, name) => [value, name]} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Task chart */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-900">Task Overview</h3>
            <div className="flex items-center gap-1 text-sm text-green-600 font-medium">
              <TrendingUp className="w-4 h-4" />
              {stats?.task_completion_rate ?? 0}% complete
            </div>
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={taskChartData} barSize={32}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#94a3b8' }} />
              <YAxis tick={{ fontSize: 12, fill: '#94a3b8' }} />
              <Tooltip />
              <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                {taskChartData.map((entry, index) => (
                  <Cell key={index} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Bottom row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Completed today */}
        <div className="card flex items-center gap-4">
          <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
            <CheckCircle className="w-6 h-6 text-green-600" />
          </div>
          <div>
            <p className="text-2xl font-bold text-gray-900">{stats?.completed_tasks_today ?? 0}</p>
            <p className="text-sm text-gray-500">Tasks completed today</p>
          </div>
        </div>

        {/* Overdue */}
        <div className="card flex items-center gap-4">
          <div className="w-12 h-12 bg-red-100 rounded-xl flex items-center justify-center">
            <AlertTriangle className="w-6 h-6 text-red-600" />
          </div>
          <div>
            <p className="text-2xl font-bold text-gray-900">{stats?.overdue_tasks ?? 0}</p>
            <p className="text-sm text-gray-500">Overdue tasks</p>
          </div>
        </div>

        {/* Surveillance */}
        <div className="card flex items-center gap-4">
          <div className="w-12 h-12 bg-orange-100 rounded-xl flex items-center justify-center">
            <Camera className="w-6 h-6 text-orange-600" />
          </div>
          <div>
            <p className="text-2xl font-bold text-gray-900">{stats?.surveillance_alerts ?? 0}</p>
            <p className="text-sm text-gray-500">Surveillance alerts</p>
          </div>
          {(stats?.surveillance_alerts ?? 0) > 0 && (
            <ArrowUpRight className="w-4 h-4 text-orange-500 ml-auto" />
          )}
        </div>
      </div>
    </div>
  )
}
