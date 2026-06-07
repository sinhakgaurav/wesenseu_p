import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Building, Pencil } from 'lucide-react'
import api from '@/lib/api'
import type { Property } from '@/lib/types'
import { Modal } from '@/components/ui/Modal'
import { PageLoader } from '@/components/ui/LoadingSpinner'
import toast from 'react-hot-toast'

export function PropertiesPage() {
  const qc = useQueryClient()
  const [showModal, setShowModal] = useState(false)
  const [editing, setEditing] = useState<Property | null>(null)
  const [form, setForm] = useState({
    name: '',
    property_type: 'Hotel',
    city: '',
    email: '',
    phone: '',
    total_rooms: 50,
    subscription_plan: 'growth',
  })

  const { data: properties = [], isLoading } = useQuery<Property[]>({
    queryKey: ['properties-admin'],
    queryFn: () => api.get('/properties').then(r => r.data),
  })

  const save = useMutation({
    mutationFn: async () => {
      if (editing) return api.patch(`/properties/${editing.id}`, form)
      return api.post('/properties', form)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['properties-admin'] })
      qc.invalidateQueries({ queryKey: ['properties'] })
      setShowModal(false)
      setEditing(null)
      toast.success(editing ? 'Property updated' : 'Property created')
    },
    onError: (err: { response?: { data?: { detail?: string } } }) => {
      toast.error(err.response?.data?.detail || 'Save failed')
    },
  })

  const deactivate = useMutation({
    mutationFn: (id: string) => api.delete(`/properties/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['properties-admin'] })
      toast.success('Property deactivated')
    },
  })

  if (isLoading) return <PageLoader />

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Properties</h1>
          <p className="text-gray-500 text-sm">Super admin: create and manage properties</p>
        </div>
        <button
          className="btn-primary flex items-center gap-2"
          onClick={() => {
            setEditing(null)
            setForm({ name: '', property_type: 'Hotel', city: '', email: '', phone: '', total_rooms: 50, subscription_plan: 'growth' })
            setShowModal(true)
          }}
        >
          <Plus className="w-4 h-4" />
          Add property
        </button>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        {properties.map(p => (
          <div key={p.id} className="card flex justify-between items-start">
            <div>
              <h3 className="font-semibold flex items-center gap-2">
                <Building className="w-4 h-4 text-blue-600" />
                {p.name}
              </h3>
              <p className="text-sm text-gray-500">{p.city} · {p.property_type}</p>
              <p className="text-xs text-gray-400 mt-1">{p.email}</p>
            </div>
            <div className="flex gap-2">
              <button
                className="p-2 hover:bg-gray-100 rounded"
                onClick={() => {
                  setEditing(p)
                  setForm({
                    name: p.name,
                    property_type: p.property_type || 'Hotel',
                    city: p.city || '',
                    email: p.email || '',
                    phone: p.phone || '',
                    total_rooms: p.total_rooms || 50,
                    subscription_plan: p.subscription_plan || 'growth',
                  })
                  setShowModal(true)
                }}
              >
                <Pencil className="w-4 h-4" />
              </button>
              <button className="text-xs text-red-600 px-2" onClick={() => deactivate.mutate(p.id)}>
                Deactivate
              </button>
            </div>
          </div>
        ))}
      </div>

      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title={editing ? 'Edit property' : 'New property'}>
        <div className="space-y-3">
          {(['name', 'property_type', 'city', 'email', 'phone'] as const).map(field => (
            <input
              key={field}
              className="input capitalize"
              placeholder={field.replace(/_/g, ' ')}
              value={form[field]}
              onChange={e => setForm({ ...form, [field]: e.target.value })}
            />
          ))}
          <input type="number" className="input" placeholder="Total rooms" value={form.total_rooms} onChange={e => setForm({ ...form, total_rooms: Number(e.target.value) })} />
          <button className="btn-primary w-full" disabled={!form.name} onClick={() => save.mutate()}>
            Save
          </button>
        </div>
      </Modal>
    </div>
  )
}
