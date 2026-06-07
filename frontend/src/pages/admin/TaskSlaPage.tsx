import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Timer, Pencil, Trash2 } from 'lucide-react'
import api from '@/lib/api'
import { Modal } from '@/components/ui/Modal'
import { PageLoader } from '@/components/ui/LoadingSpinner'
import toast from 'react-hot-toast'
import { useSelector } from 'react-redux'
import type { RootState } from '@/store'
import { useAdminPropertyId } from '@/hooks/useAdminPropertyId'
import { RequirePropertyScope } from '@/components/layout/RequirePropertyScope'

type SlaPolicy = {
  id: string
  property_id: string
  task_type: string
  service_type: string
  sla_minutes: number
  root_cause_category: string
  is_active: boolean
}

export function TaskSlaPage() {
  const qc = useQueryClient()
  const user = useSelector((s: RootState) => s.auth.user)
  const { propertyId, enabled } = useAdminPropertyId()
  const canManage = user?.role === 'property_manager' || user?.role === 'super_admin'

  const [showModal, setShowModal] = useState(false)
  const [editing, setEditing] = useState<SlaPolicy | null>(null)
  const [form, setForm] = useState({
    task_type: 'cleaning',
    service_type: '*',
    sla_minutes: 120,
    root_cause_category: '',
  })

  const { data: policies = [], isLoading } = useQuery<SlaPolicy[]>({
    queryKey: ['task-sla', propertyId],
    enabled,
    queryFn: () => api.get(`/task-sla-policies?property_id=${propertyId}`).then(r => r.data),
  })

  const save = useMutation({
    mutationFn: async () => {
      const body = { property_id: propertyId, ...form, sla_minutes: Number(form.sla_minutes) }
      if (editing) return api.patch(`/task-sla-policies/${editing.id}`, body)
      return api.post('/task-sla-policies', body)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['task-sla'] })
      setShowModal(false)
      setEditing(null)
      toast.success(editing ? 'Policy updated' : 'Policy created')
    },
  })

  const remove = useMutation({
    mutationFn: (id: string) => api.delete(`/task-sla-policies/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['task-sla'] })
      toast.success('Policy deactivated')
    },
  })

  if (isLoading) return <PageLoader />

  return (
    <RequirePropertyScope>
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Task SLA Policies</h1>
          <p className="text-gray-500 text-sm">SLA minutes and root-cause buckets by task type</p>
        </div>
        {canManage && (
          <button
            className="btn-primary flex items-center gap-2"
            onClick={() => {
              setEditing(null)
              setForm({ task_type: 'cleaning', service_type: '*', sla_minutes: 120, root_cause_category: '' })
              setShowModal(true)
            }}
          >
            <Plus className="w-4 h-4" />
            Add policy
          </button>
        )}
      </div>

      <div className="table-container">
        <table className="w-full">
          <thead className="table-header">
            <tr>
              <th className="th">Task type</th>
              <th className="th">Service</th>
              <th className="th">SLA (min)</th>
              <th className="th">Root cause</th>
              {canManage && <th className="th">Actions</th>}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {policies.map(p => (
              <tr key={p.id} className="tr-hover">
                <td className="td capitalize">{p.task_type}</td>
                <td className="td">{p.service_type}</td>
                <td className="td font-medium">{p.sla_minutes}</td>
                <td className="td text-sm text-gray-600">{p.root_cause_category}</td>
                {canManage && (
                  <td className="td">
                    <div className="flex gap-2">
                      <button
                        className="p-2 text-gray-500 hover:bg-gray-100 rounded"
                        onClick={() => {
                          setEditing(p)
                          setForm({
                            task_type: p.task_type,
                            service_type: p.service_type,
                            sla_minutes: p.sla_minutes,
                            root_cause_category: p.root_cause_category,
                          })
                          setShowModal(true)
                        }}
                      >
                        <Pencil className="w-4 h-4" />
                      </button>
                      <button className="p-2 text-red-600 hover:bg-red-50 rounded" onClick={() => remove.mutate(p.id)}>
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
        {policies.length === 0 && (
          <p className="text-center py-8 text-gray-400 flex items-center justify-center gap-2">
            <Timer className="w-5 h-5" />
            No SLA policies configured
          </p>
        )}
      </div>

      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title={editing ? 'Edit SLA policy' : 'New SLA policy'}>
        <div className="space-y-3">
          <select className="input" value={form.task_type} onChange={e => setForm({ ...form, task_type: e.target.value })}>
            {['cleaning', 'maintenance', 'laundry', 'delivery', 'other'].map(t => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
          <input className="input" placeholder="Service type (* for any)" value={form.service_type} onChange={e => setForm({ ...form, service_type: e.target.value })} />
          <input type="number" className="input" placeholder="SLA minutes" value={form.sla_minutes} onChange={e => setForm({ ...form, sla_minutes: Number(e.target.value) })} />
          <input className="input" placeholder="Root cause category" value={form.root_cause_category} onChange={e => setForm({ ...form, root_cause_category: e.target.value })} />
          <button className="btn-primary w-full" onClick={() => save.mutate()} disabled={!form.root_cause_category}>
            Save
          </button>
        </div>
      </Modal>
    </div>
    </RequirePropertyScope>
  )
}
