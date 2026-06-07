import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { CalendarClock, Clock, CheckCircle, Users, Loader2, UserCheck, UserX } from 'lucide-react'
import api from '@/lib/api'
import { useAdminPropertyId } from '@/hooks/useAdminPropertyId'
import { RequirePropertyScope } from '@/components/layout/RequirePropertyScope'

interface AttendanceSummary {
  employee_id: string; employee_name: string
  present_days: number; absent_days: number; half_days: number; leave_days: number; total_hours: number
}

interface AttendanceRecord {
  id: string; employee_id: string; property_id: string; date: string
  check_in?: string; check_out?: string; status: string; notes?: string; hours_worked?: number
}

const STATUS_COLORS: Record<string, string> = {
  present: 'bg-green-100 text-green-700',
  absent: 'bg-red-100 text-red-700',
  half_day: 'bg-yellow-100 text-yellow-700',
  leave: 'bg-blue-100 text-blue-700',
}

export function AttendancePage() {
  const { propertyId, enabled } = useAdminPropertyId()
  const now = new Date()
  const [month, setMonth] = useState(now.getMonth() + 1)
  const [year, setYear] = useState(now.getFullYear())
  const [view, setView] = useState<'summary' | 'history'>('summary')

  const { data: summary = [], isLoading: sLoading } = useQuery<AttendanceSummary[]>({
    queryKey: ['attendance-summary', month, year, propertyId],
    enabled,
    queryFn: () => api.get(`/attendance/summary?month=${month}&year=${year}&property_id=${propertyId}`).then(r => r.data),
  })

  const { data: history = [], isLoading: hLoading } = useQuery<AttendanceRecord[]>({
    queryKey: ['attendance-history', month, year, propertyId],
    queryFn: () => api.get(`/attendance/history?limit=100&from_date=${year}-${String(month).padStart(2,'0')}-01&property_id=${propertyId}`).then(r => r.data),
    enabled: enabled && view === 'history',
  })

  const presentCount = summary.filter(s => s.present_days > 0).length
  const absentCount = summary.filter(s => s.absent_days > 0).length
  const totalHours = summary.reduce((s, e) => s + e.total_hours, 0)

  const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

  const fmt = (dt?: string) => dt ? new Date(dt).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }) : '—'

  return (
    <RequirePropertyScope>
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Attendance</h1>
          <p className="text-gray-500 text-sm">Employee attendance tracking & monthly summary</p>
        </div>
        <div className="flex items-center gap-3">
          <select className="input py-2 text-sm" value={month} onChange={e => setMonth(+e.target.value)}>
            {months.map((m, i) => <option key={m} value={i + 1}>{m}</option>)}
          </select>
          <select className="input py-2 text-sm" value={year} onChange={e => setYear(+e.target.value)}>
            {[2025, 2026, 2027].map(y => <option key={y} value={y}>{y}</option>)}
          </select>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {[
          { label: 'Total Employees', count: summary.length, icon: Users, color: 'blue' },
          { label: 'Present (any day)', count: presentCount, icon: CheckCircle, color: 'green' },
          { label: 'Absent (any day)', count: absentCount, icon: UserX, color: 'red' },
          { label: 'Total Hours', count: `${totalHours.toFixed(0)}h`, icon: Clock, color: 'purple' },
        ].map(({ label, count, icon: Icon, color }) => (
          <div key={label} className="card flex items-center gap-3">
            <div className={`w-10 h-10 bg-${color}-50 rounded-xl flex items-center justify-center`}>
              <Icon className={`w-5 h-5 text-${color}-600`} />
            </div>
            <div>
              <p className="text-xl font-bold text-gray-900">{count}</p>
              <p className="text-xs text-gray-500">{label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* View toggle */}
      <div className="flex gap-2 mb-4">
        {(['summary', 'history'] as const).map(v => (
          <button key={v} onClick={() => setView(v)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors capitalize ${view === v ? 'bg-blue-600 text-white' : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'}`}>
            {v}
          </button>
        ))}
      </div>

      {view === 'summary' && (
        <div className="table-container">
          <table className="w-full">
            <thead className="table-header">
              <tr>
                <th className="th">Employee</th>
                <th className="th text-center">Present</th>
                <th className="th text-center">Absent</th>
                <th className="th text-center">Half Day</th>
                <th className="th text-center">Leave</th>
                <th className="th text-center">Total Hours</th>
                <th className="th text-center">Attendance %</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {sLoading ? (
                <tr><td colSpan={7} className="td text-center py-12">
                  <Loader2 className="w-6 h-6 animate-spin text-blue-400 mx-auto" />
                </td></tr>
              ) : summary.length === 0 ? (
                <tr><td colSpan={7} className="td text-center text-gray-400 py-12">No attendance data for this period</td></tr>
              ) : summary.map(emp => {
                const total = emp.present_days + emp.absent_days + emp.half_days + emp.leave_days
                const pct = total > 0 ? Math.round(emp.present_days / total * 100) : 0
                return (
                  <tr key={emp.employee_id} className="tr-hover">
                    <td className="td font-medium text-gray-800">{emp.employee_name}</td>
                    <td className="td text-center"><span className="bg-green-100 text-green-700 text-xs px-2 py-0.5 rounded-full">{emp.present_days}</span></td>
                    <td className="td text-center"><span className="bg-red-100 text-red-700 text-xs px-2 py-0.5 rounded-full">{emp.absent_days}</span></td>
                    <td className="td text-center"><span className="bg-yellow-100 text-yellow-700 text-xs px-2 py-0.5 rounded-full">{emp.half_days}</span></td>
                    <td className="td text-center"><span className="bg-blue-100 text-blue-700 text-xs px-2 py-0.5 rounded-full">{emp.leave_days}</span></td>
                    <td className="td text-center text-sm font-mono">{emp.total_hours}h</td>
                    <td className="td text-center">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                          <div className={`h-full rounded-full ${pct >= 90 ? 'bg-green-500' : pct >= 75 ? 'bg-yellow-500' : 'bg-red-500'}`}
                            style={{ width: `${pct}%` }} />
                        </div>
                        <span className="text-xs font-medium text-gray-600 w-10">{pct}%</span>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      {view === 'history' && (
        <div className="table-container">
          <table className="w-full">
            <thead className="table-header">
              <tr>
                <th className="th">Date</th>
                <th className="th">Check In</th>
                <th className="th">Check Out</th>
                <th className="th">Hours</th>
                <th className="th">Status</th>
                <th className="th">Notes</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {hLoading ? (
                <tr><td colSpan={6} className="td text-center py-12">
                  <Loader2 className="w-6 h-6 animate-spin text-blue-400 mx-auto" />
                </td></tr>
              ) : history.length === 0 ? (
                <tr><td colSpan={6} className="td text-center text-gray-400 py-12">No records found</td></tr>
              ) : history.map(r => (
                <tr key={r.id} className="tr-hover">
                  <td className="td font-medium text-gray-800">{r.date}</td>
                  <td className="td font-mono text-sm text-green-700">{fmt(r.check_in)}</td>
                  <td className="td font-mono text-sm text-red-600">{fmt(r.check_out)}</td>
                  <td className="td text-sm">{r.hours_worked ? `${r.hours_worked}h` : '—'}</td>
                  <td className="td">
                    <span className={`text-xs px-2 py-1 rounded-full font-medium ${STATUS_COLORS[r.status] || 'bg-gray-100 text-gray-600'}`}>
                      {r.status.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="td text-sm text-gray-500">{r.notes || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
    </RequirePropertyScope>
  )
}
