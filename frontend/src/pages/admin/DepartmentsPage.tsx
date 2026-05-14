import { useEffect, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Building2, Search, Pencil, Trash2 } from 'lucide-react'
import api from '@/lib/api'
import type { Department, Property } from '@/lib/types'
import { Modal } from '@/components/ui/Modal'
import { PageLoader } from '@/components/ui/LoadingSpinner'
import toast from 'react-hot-toast'
import { useSelector } from 'react-redux'
import type { RootState } from '@/store'

export function DepartmentsPage() {
  const qc = useQueryClient()
  const user = useSelector((state: RootState) => state.auth.user)
  const canManage = user?.role === 'property_manager' || user?.role === 'super_admin'

  const [selectedPropertyId, setSelectedPropertyId] = useState<string>('')
  const [includeInactive, setIncludeInactive] = useState(false)
  const [search, setSearch] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [editDept, setEditDept] = useState<Department | null>(null)
  const [form, setForm] = useState({ name: '', description: '' })

  const { data: properties = [] } = useQuery<Property[]>({
    queryKey: ['properties', 'all'],
    queryFn: () => api.get('/properties').then(r => r.data),
    enabled: user?.role === 'super_admin',
  })

  useEffect(() => {
    if (user?.role === 'super_admin' && properties.length && !selectedPropertyId) {
      setSelectedPropertyId(properties[0].id)
    }
  }, [user?.role, properties, selectedPropertyId])

  const effectivePropertyId = user?.role === 'super_admin' ? selectedPropertyId : (user?.property_id || '')

  const { data: departments = [], isLoading } = useQuery<Department[]>({
    queryKey: ['departments', effectivePropertyId, includeInactive],
    enabled: user?.role === 'super_admin' ? !!effectivePropertyId : !!user?.property_id,
    queryFn: async () => {
      const params = new URLSearchParams()
      if (user?.role === 'super_admin') params.set('property_id', effectivePropertyId)
      if (includeInactive) params.set('include_inactive', 'true')
      const { data } = await api.get(`/departments?${params}`)
      return data
    },
  })

  const createMut = useMutation({
    mutationFn: () =>
      api.post('/departments', {
        property_id: effectivePropertyId,
        name: form.name.trim(),
        description: form.description.trim() || undefined,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['departments'] })
      setShowCreate(false)
      setForm({ name: '', description: '' })
      toast.success('Department created')
    },
    onError: (err: unknown) => {
      const e = err as { response?: { data?: { detail?: string } } }
      toast.error(e.response?.data?.detail || 'Create failed')
    },
  })

  const patchMut = useMutation({
    mutationFn: () =>
      api.patch(`/departments/${editDept!.id}`, {
        name: form.name.trim(),
        description: form.description.trim() || undefined,
        is_active: editDept!.is_active,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['departments'] })
      setEditDept(null)
      toast.success('Department updated')
    },
    onError: (err: unknown) => {
      const e = err as { response?: { data?: { detail?: string } } }
      toast.error(e.response?.data?.detail || 'Update failed')
    },
  })

  const deleteMut = useMutation({
    mutationFn: (id: string) => api.delete(`/departments/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['departments'] })
      toast.success('Department deactivated')
    },
  })

  const filtered = departments.filter(d =>
    d.name.toLowerCase().includes(search.toLowerCase())
  )

  if (isLoading) return <PageLoader />

  if (user?.role === 'super_admin' && !effectivePropertyId) {
    return (
      <div className="p-6">
        <h1 className="page-title">Departments</h1>
        <p className="text-gray-500 text-sm mt-2">Select a property to manage departments.</p>
        {properties.length > 0 && (
          <select
            className="mt-4 border border-gray-200 rounded-lg px-3 py-2 text-sm"
            value={selectedPropertyId}
            onChange={(e) => setSelectedPropertyId(e.target.value)}
          >
            {properties.map(p => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
        )}
      </div>
    )
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title flex items-center gap-2">
            <Building2 className="w-7 h-7 text-blue-600" />
            Departments
          </h1>
          <p className="text-gray-500 text-sm">Housekeeping, F&B, security, and other operational units</p>
        </div>
        {canManage && (
          <button
            type="button"
            onClick={() => { setForm({ name: '', description: '' }); setShowCreate(true) }}
            className="btn-primary flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Add department
          </button>
        )}
      </div>

      <div className="flex flex-wrap gap-3 mb-6 items-center">
        {user?.role === 'super_admin' && properties.length > 0 && (
          <div>
            <label className="block text-xs text-gray-500 mb-1">Property</label>
            <select
              className="border border-gray-200 rounded-lg px-3 py-2 text-sm bg-white"
              value={selectedPropertyId}
              onChange={(e) => setSelectedPropertyId(e.target.value)}
            >
              {properties.map(p => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>
        )}
        <div className="relative flex-1 min-w-[200px] max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="search"
            placeholder="Search departments…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
          <input
            type="checkbox"
            checked={includeInactive}
            onChange={(e) => setIncludeInactive(e.target.checked)}
          />
          Show inactive
        </label>
      </div>

      <div className="card overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="text-left px-4 py-3 font-semibold text-gray-700">Name</th>
              <th className="text-left px-4 py-3 font-semibold text-gray-700">Description</th>
              <th className="text-left px-4 py-3 font-semibold text-gray-700">Status</th>
              {canManage && <th className="text-right px-4 py-3 font-semibold text-gray-700">Actions</th>}
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={canManage ? 4 : 3} className="px-4 py-8 text-center text-gray-400">
                  No departments yet
                </td>
              </tr>
            ) : filtered.map(d => (
              <tr key={d.id} className="border-b border-gray-100 hover:bg-gray-50/80">
                <td className="px-4 py-3 font-medium text-gray-900">{d.name}</td>
                <td className="px-4 py-3 text-gray-600 max-w-md truncate">{d.description || '—'}</td>
                <td className="px-4 py-3">
                  <span className={d.is_active ? 'text-green-600 font-medium' : 'text-gray-400'}>
                    {d.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                {canManage && (
                  <td className="px-4 py-3 text-right space-x-2">
                    <button
                      type="button"
                      className="inline-flex items-center gap-1 text-blue-600 hover:text-blue-800 text-sm"
                      onClick={() => {
                        setEditDept(d)
                        setForm({ name: d.name, description: d.description || '' })
                      }}
                    >
                      <Pencil className="w-3.5 h-3.5" /> Edit
                    </button>
                    {d.is_active && (
                      <button
                        type="button"
                        className="inline-flex items-center gap-1 text-red-600 hover:text-red-800 text-sm"
                        onClick={() => {
                          if (confirm(`Deactivate “${d.name}”?`)) deleteMut.mutate(d.id)
                        }}
                      >
                        <Trash2 className="w-3.5 h-3.5" /> Deactivate
                      </button>
                    )}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Modal isOpen={showCreate} onClose={() => setShowCreate(false)} title="New department">
        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Name</label>
            <input
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm"
              value={form.name}
              onChange={(e) => setForm(f => ({ ...f, name: e.target.value }))}
              placeholder="e.g. Housekeeping"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Description</label>
            <textarea
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm min-h-[80px]"
              value={form.description}
              onChange={(e) => setForm(f => ({ ...f, description: e.target.value }))}
              placeholder="Optional"
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" className="btn-secondary" onClick={() => setShowCreate(false)}>Cancel</button>
            <button
              type="button"
              className="btn-primary"
              disabled={!form.name.trim() || createMut.isPending}
              onClick={() => createMut.mutate()}
            >
              Create
            </button>
          </div>
        </div>
      </Modal>

      <Modal isOpen={!!editDept} onClose={() => setEditDept(null)} title="Edit department">
        {editDept && (
          <div className="space-y-3">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Name</label>
              <input
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm"
                value={form.name}
                onChange={(e) => setForm(f => ({ ...f, name: e.target.value }))}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Description</label>
              <textarea
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm min-h-[80px]"
                value={form.description}
                onChange={(e) => setForm(f => ({ ...f, description: e.target.value }))}
              />
            </div>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={editDept.is_active}
                onChange={(e) => setEditDept({ ...editDept, is_active: e.target.checked })}
              />
              Active
            </label>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" className="btn-secondary" onClick={() => setEditDept(null)}>Cancel</button>
              <button
                type="button"
                className="btn-primary"
                disabled={!form.name.trim() || patchMut.isPending}
                onClick={() => patchMut.mutate()}
              >
                Save
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
