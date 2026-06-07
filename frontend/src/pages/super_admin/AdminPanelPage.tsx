import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Building2, CheckCircle, XCircle, Users, BarChart2, Sliders, Database, Network, CreditCard, FileText, Activity } from 'lucide-react'
import { Badge } from '@/components/ui/Badge'
import api from '@/lib/api'
import toast from 'react-hot-toast'
import { SuperAdminHierarchyTab } from './SuperAdminHierarchyTab'
import { SuperAdminPlansTab } from './SuperAdminPlansTab'
import { SuperAdminCmsTab } from './SuperAdminCmsTab'
import { SuperAdminDiagnosticsTab } from './SuperAdminDiagnosticsTab'
import { SuperAdminSchemaTab } from './SuperAdminSchemaTab'

const AVAILABLE_MODULES = [
  'rooms', 'tasks', 'tickets', 'inventory', 'orders',
  'attendance', 'feedback', 'surveillance', 'verification',
  'reports', 'notifications', 'support_chat',
]

type TabId = 'stats' | 'hierarchy' | 'approvals' | 'plans' | 'cms' | 'modules' | 'employees' | 'database' | 'diagnostics'

const TABS: { id: TabId; label: string; icon: typeof Building2 }[] = [
  { id: 'stats', label: 'Stats', icon: BarChart2 },
  { id: 'hierarchy', label: 'Businesses', icon: Network },
  { id: 'approvals', label: 'Approvals', icon: CheckCircle },
  { id: 'plans', label: 'Plans', icon: CreditCard },
  { id: 'cms', label: 'CMS', icon: FileText },
  { id: 'modules', label: 'Modules', icon: Sliders },
  { id: 'employees', label: 'Employees', icon: Users },
  { id: 'database', label: 'Schema', icon: Database },
  { id: 'diagnostics', label: 'Diagnostics', icon: Activity },
]

export function AdminPanelPage() {
  const qc = useQueryClient()
  const [activeTab, setActiveTab] = useState<TabId>('stats')
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
          <p className="text-gray-500 text-sm">
            Platform control — businesses, properties, plans, CMS, approvals. Notifications: use the bell in the header.
          </p>
        </div>
      </div>

      <div className="flex gap-2 mb-6 border-b border-gray-100 overflow-x-auto">
        {TABS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={`flex items-center gap-1.5 px-3 py-2 text-sm font-medium whitespace-nowrap border-b-2 -mb-px transition-colors ${
              activeTab === id ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-800'
            }`}
          >
            <Icon className="w-4 h-4" />
            {label}
          </button>
        ))}
      </div>

      {activeTab === 'stats' && stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: 'Total Properties', value: stats.total_properties, icon: Building2 },
            { label: 'Active Properties', value: stats.active_properties, icon: CheckCircle },
            { label: 'Pending Approvals', value: stats.pending_approvals, icon: XCircle },
            { label: 'Total Employees', value: stats.total_employees, icon: Users },
            { label: 'Total Customers', value: stats.total_customers, icon: Users },
            { label: 'Total Rooms', value: stats.total_rooms, icon: BarChart2 },
            { label: 'Open Tasks', value: stats.open_tasks, icon: Sliders },
            { label: 'Open Tickets', value: stats.open_tickets, icon: Sliders },
          ].map(({ label, value, icon: Icon }) => (
            <div key={label} className="card flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-50 rounded-xl flex items-center justify-center">
                <Icon className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <p className="text-xl font-bold text-gray-900">{value}</p>
                <p className="text-xs text-gray-500">{label}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'hierarchy' && (
        <SuperAdminHierarchyTab
          onSelectProperty={(id) => {
            setSelectedPropertyId(id)
            setActiveTab('modules')
          }}
        />
      )}

      {activeTab === 'plans' && <SuperAdminPlansTab />}

      {activeTab === 'cms' && <SuperAdminCmsTab />}

      {activeTab === 'approvals' && (
        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-4">Property Approvals</h3>
          <p className="text-xs text-gray-500 mb-4">Approve or decline each property subscription. Also available under Businesses tab.</p>
          {approvals.length === 0 ? (
            <p className="text-gray-400 text-sm">No approval records found.</p>
          ) : (
            <div className="space-y-3">
              {approvals.map((a: { id: string; property_name?: string; property_id: string; status: string; requested_plan?: string; created_at: string }) => (
                <div key={a.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
                  <div>
                    <p className="font-medium text-gray-900 text-sm">{a.property_name || a.property_id}</p>
                    <p className="text-xs text-gray-500">Plan: {a.requested_plan || 'N/A'} · {new Date(a.created_at).toLocaleDateString()}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <Badge variant={statusColor[a.status] || 'gray'}>{a.status}</Badge>
                    {a.status === 'pending' && (
                      <>
                        <button onClick={() => approvalAction.mutate({ approvalId: a.id, status: 'approved' })} className="btn-primary text-xs px-3 py-1">Approve</button>
                        <button onClick={() => approvalAction.mutate({ approvalId: a.id, status: 'rejected' })} className="btn-secondary text-xs px-3 py-1 text-red-600">Decline</button>
                      </>
                    )}
                    {a.status === 'approved' && (
                      <button onClick={() => approvalAction.mutate({ approvalId: a.id, status: 'suspended' })} className="btn-secondary text-xs px-3 py-1 text-orange-600">Suspend</button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'modules' && (
        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-2">Module Configuration</h3>
          <p className="text-xs text-gray-500 mb-4">Pick a property from the Businesses tab, or paste UUID below.</p>
          <input
            type="text"
            placeholder="Property UUID..."
            value={selectedPropertyId || ''}
            onChange={e => setSelectedPropertyId(e.target.value)}
            className="input-field flex-1 max-w-md mb-4"
          />
          {selectedPropertyId && moduleConfigs.length > 0 ? (
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {moduleConfigs.map((cfg: { module_name: string; is_enabled: boolean }) => (
                <div key={cfg.module_name} className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
                  <span className="text-sm font-medium text-gray-800 capitalize">{cfg.module_name.replace(/_/g, ' ')}</span>
                  <button
                    onClick={() => toggleModule.mutate({ module: cfg.module_name, enabled: !cfg.is_enabled })}
                    className={`relative inline-flex h-6 w-11 rounded-full transition-colors ${cfg.is_enabled ? 'bg-blue-500' : 'bg-gray-200'}`}
                  >
                    <span className={`inline-block h-5 w-5 transform rounded-full bg-white shadow transition-transform mt-0.5 ${cfg.is_enabled ? 'translate-x-5' : 'translate-x-0.5'}`} />
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-400 text-sm">Select a property to manage modules (notifications, surveillance, etc.).</p>
          )}
        </div>
      )}

      {activeTab === 'database' && <SuperAdminSchemaTab />}

      {activeTab === 'diagnostics' && <SuperAdminDiagnosticsTab />}

      {activeTab === 'employees' && (
        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-4">All Employees (cross-property)</h3>
          {employees.length === 0 ? (
            <p className="text-gray-400 text-sm">No employees found.</p>
          ) : (
            <div className="space-y-2">
              {employees.map((e: { id: string; full_name: string; email: string; role: string; status: string }) => (
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
