import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Truck, Trash2 } from 'lucide-react'
import api from '@/lib/api'
import { Modal } from '@/components/ui/Modal'
import { PageLoader } from '@/components/ui/LoadingSpinner'
import toast from 'react-hot-toast'
import { useAdminPropertyId } from '@/hooks/useAdminPropertyId'
import { RequirePropertyScope } from '@/components/layout/RequirePropertyScope'

type Vendor = {
  id: string
  name: string
  contact_person?: string
  phone?: string
  email?: string
}

export function VendorsPage() {
  const qc = useQueryClient()
  const { propertyId, enabled } = useAdminPropertyId()
  const [showModal, setShowModal] = useState(false)
  const [form, setForm] = useState({ name: '', contact_person: '', phone: '', email: '' })

  const { data: vendors = [], isLoading } = useQuery<Vendor[]>({
    queryKey: ['vendors', propertyId],
    enabled: !!propertyId,
    queryFn: () => api.get(`/vendors?property_id=${propertyId}`).then(r => r.data),
  })

  const create = useMutation({
    mutationFn: () => api.post('/vendors', { property_id: propertyId, ...form }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['vendors'] })
      setShowModal(false)
      toast.success('Vendor added')
    },
  })

  const remove = useMutation({
    mutationFn: (id: string) => api.delete(`/vendors/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['vendors'] })
      toast.success('Vendor removed')
    },
  })

  if (isLoading) return <PageLoader />

  return (
    <RequirePropertyScope>
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title flex items-center gap-2">
            <Truck className="w-7 h-7 text-blue-600" />
            Vendors
          </h1>
          <p className="text-gray-500 text-sm">Procurement contacts for inventory</p>
        </div>
        <button className="btn-primary flex items-center gap-2" onClick={() => setShowModal(true)}>
          <Plus className="w-4 h-4" />
          Add vendor
        </button>
      </div>
      <div className="card divide-y">
        {vendors.map(v => (
          <div key={v.id} className="py-3 flex justify-between items-center px-4">
            <div>
              <p className="font-medium">{v.name}</p>
              <p className="text-sm text-gray-500">{v.contact_person} · {v.phone}</p>
            </div>
            <button className="text-red-600 p-2" onClick={() => remove.mutate(v.id)}>
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        ))}
        {vendors.length === 0 && <p className="py-8 text-center text-gray-400">No vendors yet.</p>}
      </div>
      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="New vendor">
        <div className="space-y-3">
          <input className="input" placeholder="Name" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} />
          <input className="input" placeholder="Contact person" value={form.contact_person} onChange={e => setForm({ ...form, contact_person: e.target.value })} />
          <input className="input" placeholder="Phone" value={form.phone} onChange={e => setForm({ ...form, phone: e.target.value })} />
          <input className="input" placeholder="Email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} />
          <button className="btn-primary w-full" disabled={!form.name} onClick={() => create.mutate()}>Save</button>
        </div>
      </Modal>
    </div>
    </RequirePropertyScope>
  )
}
