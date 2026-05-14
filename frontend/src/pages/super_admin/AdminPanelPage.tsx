import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { Building2, CheckCircle, XCircle, Users, BarChart2, Sliders, PlusCircle } from 'lucide-react'
import { Badge } from '@/components/ui/Badge'
import api from '@/lib/api'
import toast from 'react-hot-toast'

const AVAILABLE_MODULES = [
  'rooms', 'tasks', 'tickets', 'inventory', 'orders',
  'attendance', 'feedback', 'surveillance', 'verification',
  'reports', 'notifications', 'support_chat',
]

export function AdminPanelPage() {
  const qc = useQueryClient()
  const [activeTab, setActiveTab] = useState<'stats' | 'approvals' | 'modules' | 'employees'>('stats')
  const [selectedPropertyId, setSelectedPropertyId] = useState<string | null>(null)

  const { data: stats } = useQuery({
    queryKey: ['admin-stats'],
    queryFn: () => api.get('/admin/stats').then(r => r.data),
  })

  const { data: approvals = [] } = useQuery({
    queryKey: ['admin-approvals'],
    queryFn: () => api.get('/admin/approvals').then(r => r.data),
    enabled: activeTab === 'approvals',
  })

  const { data: employees = [] } = useQuery({
    queryKey: ['admin-employees'],
    queryFn: () => api.get('/admin/employees').then(r => r.data),
    enabled: activeTab === 'employees',
  })

  const { data: moduleConfigs = [] } = useQuery({
    queryKey: ['admin-modules', selectedPropertyId],
    queryFn: () => api.get(`/admin/modules/${selectedPropertyId}`).then(r => r.data),
    enabled: !!selectedPropertyId && activeTab === 'modules',
  })

  const approvalAction = useMutation({
    mutationFn: ({ approvalId, status, notes }: { approvalId: string; status: string; notes?: string }) =>
      api.patch(`/admin/approvals/${approvalId}`, { status, notes }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin-approvals'] }); toast.success('Approval updated') },
  })

  const toggleModule = useMutation({
    mutationFn: ({ module, enabled }: { module: string; enabled: boolean }) =>
      api.patch(`/admin/modules/${selectedPropertyId}/${module}`, { is_enabled: enabled }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin-modules'] }) },
  })

  const statusColor: Record<string, string> = { pending: 'yellow', approved: 'green', rejected: 'red', suspended: 'orange', under_review: 'blue' }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Super Admin Panel</h1>
          <p className="text-gray-500 text-sm">Full platform control — approvals, modules, employees</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 border-b border-gray-100">
        {(['stats', 'approvals', 'modules', 'employees'] as const).map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm font-medium capitalize border-b-2 -mb-px transition-colors ${
              activeTab === tab ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-800'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Stats */}
      {activeTab === 'stats' && stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: 'Total Properties', value: stats.total_properties, icon: Building2, color: 'blue' },
            { label: 'Active Properties', value: stats.active_properties, icon: CheckCircle, color: 'green' },
            { label: 'Pending Approvals', value: stats.pending_approvals, icon: XCircle, color: 'yellow' },
            { label: 'Total Employees', value: stats.total_employees, icon: Users, color: 'purple' },
            { label: 'Total Customers', value: stats.total_customers, icon: Users, color: 'indigo' },
            { label: 'Total Rooms', value: stats.total_rooms, icon: BarChart2, color: 'teal' },
            { label: 'Open Tasks', value: stats.open_tasks, icon: Sliders, color: 'orange' },
            { label: 'Open Tickets', value: stats.open_tickets, icon: Sliders, color: 'red' },
          ].map(({ label, value, icon: Icon, color }) => (
            <div key={label} className="card flex items-center gap-3">
              <div className={`w-10 h-10 bg-${color}-50 rounded-xl flex items-center justify-center`}>
                <Icon className={`w-5 h-5 text-${color}-600`} />
              </div>
              <div>
                <p className="text-xl font-bold text-gray-900">{value}</p>
                <p className="text-xs text-gray-500">{label}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Approvals */}
      {activeTab === 'approvals' && (
        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-4">Property Approvals</h3>
          {approvals.length === 0 ? (
            <p className="text-gray-400 text-sm">No approval records found.</p>
          ) : (
            <div className="space-y-3">
              {approvals.map((a: any) => (
                <div key={a.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
                  <div>
                    <p className="font-medium text-gray-900 text-sm">{a.property_name || a.property_id}</p>
                    <p className="text-xs text-gray-500">Plan: {a.requested_plan || 'N/A'} · {new Date(a.created_at).toLocaleDateString()}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <Badge variant={statusColor[a.status] || 'gray'}>{a.status}</Badge>
                    {a.status === 'pending' && (
                      <>
                        <button
                          onClick={() => approvalAction.mutate({ approvalId: a.id, status: 'approved' })}
                          className="btn-primary text-xs px-3 py-1"
                        >
                          Approve
                        </button>
                        <button
                          onClick={() => approvalAction.mutate({ approvalId: a.id, status: 'rejected' })}
                          className="btn-secondary text-xs px-3 py-1 text-red-600"
                        >
                          Reject
                        </button>
                      </>
                    )}
                    {a.status === 'approved' && (
                      <button
                        onClick={() => approvalAction.mutate({ approvalId: a.id, status: 'suspended' })}
                        className="btn-secondary text-xs px-3 py-1 text-orange-600"
                      >
                        Suspend
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Module config */}
      {activeTab === 'modules' && (
        <div className="card">
          <div className="flex items-center gap-4 mb-6">
            <h3 className="font-semibold text-gray-900">Module Configuration</h3>
            <input
              type="text"
              placeholder="Enter property UUID..."
              value={selectedPropertyId || ''}
              onChange={e => setSelectedPropertyId(e.target.value)}
              className="input-field flex-1 max-w-xs"
            />
          </div>
          {selectedPropertyId && moduleConfigs.length > 0 ? (
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {moduleConfigs.map((cfg: any) => (
                <div key={cfg.module_name} className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
                  <span className="text-sm font-medium text-gray-800 capitalize">{cfg.module_name.replace(/_/g, ' ')}</span>
                  <button
                    onClick={() => toggleModule.mutate({ module: cfg.module_name, enabled: !cfg.is_enabled })}
                    className={`relative inline-flex h-6 w-11 rounded-full transition-colors ${
                      cfg.is_enabled ? 'bg-blue-500' : 'bg-gray-200'
                    }`}
                  >
                    <span className={`inline-block h-5 w-5 transform rounded-full bg-white shadow transition-transform mt-0.5 ${
                      cfg.is_enabled ? 'translate-x-5' : 'translate-x-0.5'
                    }`} />
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-400 text-sm">Enter a property UUID above to manage its modules.</p>
          )}
        </div>
      )}

      {/* Employees */}
      {activeTab === 'employees' && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-900">All Employees</h3>
          </div>
          {employees.length === 0 ? (
            <p className="text-gray-400 text-sm">No employees found.</p>
          ) : (
            <div className="space-y-2">
              {employees.map((e: any) => (
                <div key={e.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
                  <div>
                    <p className="font-medium text-gray-900 text-sm">{e.full_name}</p>
                    <p className="text-xs text-gray-500">{e.email} · {e.role}</p>
                  </div>
                  <Badge variant={e.status === 'active' ? 'green' : 'gray'}>{e.status}</Badge>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
