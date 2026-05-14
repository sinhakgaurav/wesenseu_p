import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Shirt, Plus } from 'lucide-react'
import api from '@/lib/api'
import toast from 'react-hot-toast'
import { useSelector } from 'react-redux'
import type { RootState } from '@/store'
import { Modal } from '@/components/ui/Modal'
import { PageLoader } from '@/components/ui/LoadingSpinner'

export function LaundryPage() {
  const qc = useQueryClient()
  const user = useSelector((s: RootState) => s.auth.user)
  const propertyId = user?.property_id
  const [showNew, setShowNew] = useState(false)
  const [form, setForm] = useState({ guest_name: '', guest_phone: '', notes: '', item_desc: 'Guest laundry', qty: 1 })

  const { data: orders = [], isLoading } = useQuery({
    queryKey: ['laundry', propertyId],
    queryFn: () => api.get(`/laundry?property_id=${propertyId}`).then(r => r.data),
    enabled: !!propertyId,
  })

  const createMut = useMutation({
    mutationFn: () =>
      api.post('/laundry', {
        property_id: propertyId,
        guest_name: form.guest_name || undefined,
        guest_phone: form.guest_phone || undefined,
        notes: form.notes || undefined,
        items: [{ description: form.item_desc, quantity: Number(form.qty), service_type: 'wash' }],
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['laundry'] })
      setShowNew(false)
      toast.success('Laundry order created')
    },
  })

  const statusMut = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) => api.patch(`/laundry/${id}`, { status }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['laundry'] })
      toast.success('Updated')
    },
  })

  if (!propertyId) return <p className="text-gray-500">No property context.</p>
  if (isLoading) return <PageLoader />

  const next = (cur: string) => {
    const seq = ['received', 'collected', 'washing', 'drying', 'ironing', 'ready', 'delivered']
    const i = seq.indexOf(cur)
    return i >= 0 && i < seq.length - 1 ? seq[i + 1] : cur
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Laundry</h1>
          <p className="text-gray-500 text-sm">Track wash / dry-clean orders by guest or room</p>
        </div>
        <button className="btn-primary flex items-center gap-2" onClick={() => setShowNew(true)}>
          <Plus className="w-4 h-4" /> New order
        </button>
      </div>

      <div className="space-y-3">
        {orders.map((o: any) => (
          <div key={o.id} className="card flex items-start justify-between gap-4">
            <div className="flex gap-3">
              <div className="w-10 h-10 bg-indigo-50 rounded-xl flex items-center justify-center">
                <Shirt className="w-5 h-5 text-indigo-600" />
              </div>
              <div>
                <p className="font-medium text-gray-900 capitalize">{o.status.replace(/_/g, ' ')}</p>
                <p className="text-sm text-gray-500">
                  {o.guest_name || 'Walk-in'} {o.guest_phone ? `· ${o.guest_phone}` : ''}
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  {(o.items || []).map((it: any) => `${it.quantity}× ${it.description}`).join(', ') || 'No line items'}
                </p>
              </div>
            </div>
            {o.status !== 'delivered' && o.status !== 'cancelled' && (
              <button
                className="btn-secondary text-xs"
                onClick={() => statusMut.mutate({ id: o.id, status: next(o.status) })}
              >
                Advance → {next(o.status)}
              </button>
            )}
          </div>
        ))}
        {orders.length === 0 && <p className="text-gray-400 text-sm">No laundry orders yet.</p>}
      </div>

      <Modal isOpen={showNew} onClose={() => setShowNew(false)} title="New laundry order">
        <div className="space-y-3">
          <input className="input" placeholder="Guest name" value={form.guest_name} onChange={(e) => setForm({ ...form, guest_name: e.target.value })} />
          <input className="input" placeholder="Phone" value={form.guest_phone} onChange={(e) => setForm({ ...form, guest_phone: e.target.value })} />
          <input className="input" placeholder="Item description" value={form.item_desc} onChange={(e) => setForm({ ...form, item_desc: e.target.value })} />
          <input className="input" type="number" min={1} placeholder="Qty" value={form.qty} onChange={(e) => setForm({ ...form, qty: Number(e.target.value) })} />
          <textarea className="input" rows={2} placeholder="Notes" value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
          <button className="btn-primary w-full" disabled={createMut.isPending} onClick={() => createMut.mutate()}>
            Create
          </button>
        </div>
      </Modal>
    </div>
  )
}
