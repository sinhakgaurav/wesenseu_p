import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Pencil, Trash2, FolderTree } from 'lucide-react'
import api from '@/lib/api'
import type { PropertyGroup } from '@/lib/types'
import { Modal } from '@/components/ui/Modal'
import { PageLoader } from '@/components/ui/LoadingSpinner'
import toast from 'react-hot-toast'
import { useSelector } from 'react-redux'
import type { RootState } from '@/store'

export function PropertyGroupsPage() {
  const qc = useQueryClient()
  const user = useSelector((s: RootState) => s.auth.user)
  const canManage = user?.role === 'super_admin' || user?.role === 'property_manager'

  const [showModal, setShowModal] = useState(false)
  const [editing, setEditing] = useState<PropertyGroup | null>(null)
  const [form, setForm] = useState({ name: '', description: '', customer_id: '' })

  const { data: groups = [], isLoading } = useQuery<PropertyGroup[]>({
    queryKey: ['property-groups', user?.role],
    queryFn: async () => {
      const { data } = await api.get('/property-groups')
      return data
    },
  })

  const saveMutation = useMutation({
    mutationFn: async () => {
      const payload: Record<string, unknown> = {
        name: form.name.trim(),
        description: form.description.trim() || undefined,
      }
      if (user?.role === 'super_admin' && form.customer_id.trim()) {
        payload.customer_id = form.customer_id.trim()
      }
      if (editing) {
        await api.patch(`/property-groups/${editing.id}`, payload)
      } else {
        await api.post('/property-groups', payload)
      }
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['property-groups'] })
      qc.invalidateQueries({ queryKey: ['properties'] })
      setShowModal(false)
      setEditing(null)
      toast.success(editing ? 'Group updated' : 'Group created')
    },
    onError: () => toast.error('Save failed'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/property-groups/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['property-groups'] })
      toast.success('Group deactivated')
    },
  })

  if (isLoading) return <PageLoader />

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title flex items-center gap-2">
            <FolderTree className="w-7 h-7 text-blue-600" />
            Property groups
          </h1>
          <p className="text-gray-500 text-sm">
            Portfolio groupings under a B2B owner. Assign properties to a group from Properties (super admin).
          </p>
        </div>
        {canManage && (
          <button
            type="button"
            onClick={() => {
              setEditing(null)
              setForm({ name: '', description: '', customer_id: '' })
              setShowModal(true)
            }}
            className="btn-primary flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Add group
          </button>
        )}
      </div>

      <div className="card overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="text-left p-3 font-medium text-gray-600">Name</th>
              <th className="text-left p-3 font-medium text-gray-600">Customer</th>
              <th className="text-left p-3 font-medium text-gray-600">Active</th>
              {canManage && <th className="text-right p-3 font-medium text-gray-600">Actions</th>}
            </tr>
          </thead>
          <tbody>
            {groups.map((g) => (
              <tr key={g.id} className="border-b border-gray-100 hover:bg-gray-50/80">
                <td className="p-3 font-medium text-gray-900">{g.name}</td>
                <td className="p-3 font-mono text-xs text-gray-500">{g.customer_id || '—'}</td>
                <td className="p-3">{g.is_active ? 'Yes' : 'No'}</td>
                {canManage && (
                  <td className="p-3 text-right space-x-2">
                    <button
                      type="button"
                      onClick={() => {
                        setEditing(g)
                        setForm({
                          name: g.name,
                          description: g.description || '',
                          customer_id: g.customer_id || '',
                        })
                        setShowModal(true)
                      }}
                      className="p-1.5 rounded-lg text-blue-600 hover:bg-blue-50 inline-flex"
                    >
                      <Pencil className="w-4 h-4" />
                    </button>
                    {g.is_active && (
                      <button
                        type="button"
                        onClick={() => {
                          if (confirm(`Deactivate group "${g.name}"?`)) deleteMutation.mutate(g.id)
                        }}
                        className="p-1.5 rounded-lg text-red-500 hover:bg-red-50 inline-flex"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
        {groups.length === 0 && (
          <p className="p-8 text-center text-gray-500">No property groups yet.</p>
        )}
      </div>

      <Modal
        isOpen={showModal}
        onClose={() => { setShowModal(false); setEditing(null) }}
        title={editing ? 'Edit property group' : 'New property group'}
      >
        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
            <input
              className="input"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="e.g. North region portfolio"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <input
              className="input"
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
            />
          </div>
          {user?.role === 'super_admin' && !editing && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Customer ID (optional)</label>
              <input
                className="input font-mono text-xs"
                value={form.customer_id}
                onChange={(e) => setForm({ ...form, customer_id: e.target.value })}
                placeholder="UUID of B2B customer owner"
              />
              <p className="text-xs text-gray-400 mt-1">Leave empty for an unassigned portfolio shell.</p>
            </div>
          )}
          <div className="flex gap-2 pt-2">
            <button type="button" className="btn-secondary flex-1" onClick={() => setShowModal(false)}>
              Cancel
            </button>
            <button
              type="button"
              className="btn-primary flex-1"
              disabled={saveMutation.isPending || !form.name.trim()}
              onClick={() => saveMutation.mutate()}
            >
              {saveMutation.isPending ? 'Saving…' : 'Save'}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
