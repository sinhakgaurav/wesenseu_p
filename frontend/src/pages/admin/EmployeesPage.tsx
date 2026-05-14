import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Users, Search, Phone, Mail } from 'lucide-react'
import api from '@/lib/api'
import type { Employee } from '@/lib/types'
import { Badge, StatusBadge } from '@/components/ui/Badge'
import { Modal } from '@/components/ui/Modal'
import { PageLoader } from '@/components/ui/LoadingSpinner'
import toast from 'react-hot-toast'
import { useSelector } from 'react-redux'
import type { RootState } from '@/store'

const ROLES = ['property_manager', 'dept_manager', 'employee']
const SHIFTS = ['morning', 'afternoon', 'night', 'rotational']

export function EmployeesPage() {
  const queryClient = useQueryClient()
  const user = useSelector((state: RootState) => state.auth.user)

  const [searchQuery, setSearchQuery] = useState('')
  const [filterRole, setFilterRole] = useState('')
  const [filterStatus, setFilterStatus] = useState('active')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [selectedEmployee, setSelectedEmployee] = useState<Employee | null>(null)

  const [newEmployee, setNewEmployee] = useState({
    full_name: '',
    email: '',
    phone: '',
    role: 'employee',
    shift_type: 'morning',
    salary: '',
    password: 'Password@123',
    property_id: user?.property_id || '',
  })

  const { data: employees = [], isLoading } = useQuery<Employee[]>({
    queryKey: ['employees', user?.property_id, filterRole, filterStatus],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (user?.property_id) params.set('property_id', user.property_id)
      if (filterRole) params.set('role', filterRole)
      if (filterStatus) params.set('status', filterStatus)
      params.set('limit', '100')
      const { data } = await api.get(`/employees?${params}`)
      return data
    },
  })

  const createMutation = useMutation({
    mutationFn: (data: typeof newEmployee) => api.post('/employees', {
      ...data,
      salary: data.salary ? Number(data.salary) : undefined,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['employees'] })
      setShowCreateModal(false)
      toast.success('Employee created')
    },
    onError: (err: unknown) => {
      const error = err as { response?: { data?: { detail?: string } } }
      toast.error(error.response?.data?.detail || 'Failed to create employee')
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Employee> }) => api.patch(`/employees/${id}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['employees'] })
      setSelectedEmployee(null)
      toast.success('Employee updated')
    },
  })

  const filtered = employees.filter(e =>
    e.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    e.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
    e.employee_code.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const roleColor: Record<string, string> = {
    super_admin: 'purple',
    property_manager: 'blue',
    dept_manager: 'indigo',
    employee: 'gray',
  }

  if (isLoading) return <PageLoader />

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Employees</h1>
          <p className="text-gray-500 text-sm">{employees.length} team members</p>
        </div>
        <button onClick={() => setShowCreateModal(true)} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" />
          Add Employee
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search employees..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10 pr-4 py-2 border border-gray-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <select className="border border-gray-200 rounded-lg px-3 py-2 text-sm bg-white" value={filterRole} onChange={(e) => setFilterRole(e.target.value)}>
          <option value="">All Roles</option>
          {ROLES.map(r => <option key={r} value={r}>{r.replace(/_/g, ' ')}</option>)}
        </select>
        <select className="border border-gray-200 rounded-lg px-3 py-2 text-sm bg-white" value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
          <option value="">All Status</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
        </select>
      </div>

      {/* Employees grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {filtered.map((emp) => (
          <div
            key={emp.id}
            onClick={() => setSelectedEmployee(emp)}
            className="bg-white rounded-xl border border-gray-100 p-5 hover:shadow-md cursor-pointer transition-all"
          >
            <div className="flex items-start gap-3">
              <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center text-white font-bold text-lg flex-shrink-0">
                {emp.full_name[0].toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-semibold text-gray-900 truncate">{emp.full_name}</p>
                <p className="text-xs text-gray-400 font-mono">{emp.employee_code}</p>
              </div>
            </div>

            <div className="mt-3 space-y-1.5">
              <div className="flex items-center gap-2">
                <Badge variant={roleColor[emp.role] || 'gray'}>
                  {emp.role.replace(/_/g, ' ')}
                </Badge>
                <StatusBadge status={emp.status} />
              </div>
              {emp.shift_type && (
                <p className="text-xs text-gray-500 capitalize">{emp.shift_type} shift</p>
              )}
            </div>

            <div className="mt-3 space-y-1">
              {emp.phone && (
                <div className="flex items-center gap-2 text-xs text-gray-500">
                  <Phone className="w-3 h-3" />
                  {emp.phone}
                </div>
              )}
              <div className="flex items-center gap-2 text-xs text-gray-500">
                <Mail className="w-3 h-3" />
                <span className="truncate">{emp.email}</span>
              </div>
            </div>

            <div className="mt-3 pt-3 border-t border-gray-50 flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <div className={`w-2 h-2 rounded-full ${emp.is_available ? 'bg-green-500' : 'bg-gray-300'}`} />
                <span className="text-xs text-gray-500">{emp.is_available ? 'Available' : 'Busy'}</span>
              </div>
            </div>
          </div>
        ))}

        {filtered.length === 0 && (
          <div className="col-span-full text-center py-12 text-gray-400">
            <Users className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>No employees found</p>
          </div>
        )}
      </div>

      {/* Create Modal */}
      <Modal isOpen={showCreateModal} onClose={() => setShowCreateModal(false)} title="Add Employee">
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
              <input className="input" value={newEmployee.full_name} onChange={(e) => setNewEmployee({ ...newEmployee, full_name: e.target.value })} placeholder="Employee name" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input type="email" className="input" value={newEmployee.email} onChange={(e) => setNewEmployee({ ...newEmployee, email: e.target.value })} placeholder="email@example.com" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
              <input className="input" value={newEmployee.phone} onChange={(e) => setNewEmployee({ ...newEmployee, phone: e.target.value })} placeholder="+91 XXXXX XXXXX" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
              <select className="input" value={newEmployee.role} onChange={(e) => setNewEmployee({ ...newEmployee, role: e.target.value })}>
                {ROLES.map(r => <option key={r} value={r}>{r.replace(/_/g, ' ')}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Shift</label>
              <select className="input" value={newEmployee.shift_type} onChange={(e) => setNewEmployee({ ...newEmployee, shift_type: e.target.value })}>
                {SHIFTS.map(s => <option key={s}>{s}</option>)}
              </select>
            </div>
            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">Monthly Salary (₹)</label>
              <input type="number" className="input" value={newEmployee.salary} onChange={(e) => setNewEmployee({ ...newEmployee, salary: e.target.value })} placeholder="25000" />
            </div>
            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
              <input type="password" className="input" value={newEmployee.password} onChange={(e) => setNewEmployee({ ...newEmployee, password: e.target.value })} />
            </div>
          </div>
          <div className="flex gap-3 pt-2">
            <button onClick={() => setShowCreateModal(false)} className="btn-secondary flex-1">Cancel</button>
            <button
              onClick={() => createMutation.mutate(newEmployee)}
              disabled={createMutation.isPending || !newEmployee.full_name || !newEmployee.email}
              className="btn-primary flex-1"
            >
              {createMutation.isPending ? 'Creating...' : 'Add Employee'}
            </button>
          </div>
        </div>
      </Modal>

      {/* Employee Detail Modal */}
      {selectedEmployee && (
        <Modal isOpen={!!selectedEmployee} onClose={() => setSelectedEmployee(null)} title={selectedEmployee.full_name}>
          <div className="space-y-4">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center text-white font-bold text-2xl">
                {selectedEmployee.full_name[0]}
              </div>
              <div>
                <p className="font-semibold text-lg text-gray-900">{selectedEmployee.full_name}</p>
                <p className="text-sm text-gray-500">{selectedEmployee.employee_code}</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              {[
                { label: 'Role', value: selectedEmployee.role.replace(/_/g, ' ') },
                { label: 'Shift', value: selectedEmployee.shift_type || '-' },
                { label: 'Email', value: selectedEmployee.email },
                { label: 'Phone', value: selectedEmployee.phone || '-' },
                { label: 'Salary', value: selectedEmployee.salary ? `₹${selectedEmployee.salary.toLocaleString()}` : '-' },
                { label: 'Status', value: selectedEmployee.status },
              ].map(({ label, value }) => (
                <div key={label} className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-500">{label}</p>
                  <p className="text-sm font-medium text-gray-900 mt-0.5 capitalize">{value}</p>
                </div>
              ))}
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => updateMutation.mutate({
                  id: selectedEmployee.id,
                  data: { status: selectedEmployee.status === 'active' ? 'inactive' : 'active' },
                })}
                className={selectedEmployee.status === 'active' ? 'btn-danger flex-1' : 'btn-success flex-1'}
              >
                {selectedEmployee.status === 'active' ? 'Deactivate' : 'Activate'}
              </button>
              <button
                onClick={() => updateMutation.mutate({
                  id: selectedEmployee.id,
                  data: { is_available: !selectedEmployee.is_available },
                })}
                className="btn-secondary flex-1"
              >
                Mark {selectedEmployee.is_available ? 'Unavailable' : 'Available'}
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  )
}
