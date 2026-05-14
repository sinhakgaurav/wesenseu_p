import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ShoppingCart, Clock, CheckCircle, Package, Plus, X, ChefHat, Loader2 } from 'lucide-react'
import { StatusBadge } from '@/components/ui/Badge'
import { useSelector } from 'react-redux'
import type { RootState } from '@/store'
import api from '@/lib/api'

interface OrderItem { item_name: string; quantity: number; unit_price: number }
interface Order {
  id: string; order_number: string; room_id: string; property_id: string
  order_type: string; total_amount: number; status: string
  guest_name?: string; notes?: string; assigned_to?: string
  delivered_at?: string; created_at: string; items: OrderItem[]
}

const STATUS_FLOW: Record<string, string> = {
  pending: 'confirmed', confirmed: 'preparing', preparing: 'out_for_delivery',
  out_for_delivery: 'delivered',
}
const STATUS_LABEL: Record<string, string> = {
  pending: 'Confirm', confirmed: 'Start Preparing', preparing: 'Out for Delivery',
  out_for_delivery: 'Mark Delivered',
}
const ORDER_TYPES = ['food', 'service', 'amenity', 'extra_bed', 'laundry']

export function OrdersPage() {
  const queryClient = useQueryClient()
  const { user } = useSelector((s: RootState) => s.auth)
  const [showForm, setShowForm] = useState(false)
  const [filter, setFilter] = useState('')
  const [form, setForm] = useState({
    order_type: 'food', guest_name: '', notes: '',
    room_id: '', items: [{ item_name: '', quantity: 1, unit_price: 0 }],
  })

  const { data: orders = [], isLoading } = useQuery<Order[]>({
    queryKey: ['orders'],
    queryFn: () => api.get('/orders').then(r => r.data),
  })

  const { data: rooms = [] } = useQuery<any[]>({
    queryKey: ['rooms'],
    queryFn: () => api.get('/rooms').then(r => r.data),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      api.patch(`/orders/${id}`, { status }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['orders'] }),
  })

  const createMutation = useMutation({
    mutationFn: (data: any) => api.post('/orders', data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['orders'] }); setShowForm(false) },
  })

  const handleCreate = () => {
    createMutation.mutate({
      property_id: user?.property_id,
      room_id: form.room_id,
      order_type: form.order_type,
      guest_name: form.guest_name,
      notes: form.notes,
      items: form.items.filter(i => i.item_name),
    })
  }

  const filtered = filter ? orders.filter(o => o.status === filter) : orders
  const pending = orders.filter(o => o.status === 'pending').length
  const preparing = orders.filter(o => ['confirmed', 'preparing'].includes(o.status)).length
  const delivered = orders.filter(o => o.status === 'delivered').length
  const revenue = orders.filter(o => o.status === 'delivered').reduce((s, o) => s + o.total_amount, 0)

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Orders</h1>
          <p className="text-gray-500 text-sm">Room service & guest requests</p>
        </div>
        <button onClick={() => setShowForm(true)} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> New Order
        </button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {[
          { label: 'Pending', count: pending, icon: Clock, color: 'yellow' },
          { label: 'In Progress', count: preparing, icon: ChefHat, color: 'blue' },
          { label: 'Delivered Today', count: delivered, icon: CheckCircle, color: 'green' },
          { label: 'Revenue', count: `₹${revenue.toLocaleString()}`, icon: ShoppingCart, color: 'purple' },
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

      {/* Filter bar */}
      <div className="flex gap-2 mb-4">
        {['', 'pending', 'confirmed', 'preparing', 'out_for_delivery', 'delivered', 'cancelled'].map(s => (
          <button key={s} onClick={() => setFilter(s)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${filter === s ? 'bg-blue-600 text-white' : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'}`}>
            {s === '' ? 'All' : s.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="flex justify-center py-16"><Loader2 className="w-8 h-8 animate-spin text-blue-500" /></div>
      ) : (
        <div className="table-container">
          <table className="w-full">
            <thead className="table-header">
              <tr>
                <th className="th">Order #</th>
                <th className="th">Room</th>
                <th className="th">Guest</th>
                <th className="th">Type</th>
                <th className="th">Items</th>
                <th className="th">Amount</th>
                <th className="th">Status</th>
                <th className="th">Time</th>
                <th className="th">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {filtered.length === 0 ? (
                <tr><td colSpan={9} className="td text-center text-gray-400 py-12">No orders found</td></tr>
              ) : filtered.map((order) => {
                const room = rooms.find(r => r.id === order.room_id)
                const nextStatus = STATUS_FLOW[order.status]
                return (
                  <tr key={order.id} className="tr-hover">
                    <td className="td font-mono text-sm font-medium">{order.order_number}</td>
                    <td className="td font-semibold">{room?.room_number || '—'}</td>
                    <td className="td">{order.guest_name || '—'}</td>
                    <td className="td">
                      <span className="bg-blue-50 text-blue-700 text-xs px-2 py-1 rounded-full capitalize">{order.order_type}</span>
                    </td>
                    <td className="td text-sm text-gray-500">
                      {order.items?.length ? order.items.map(i => `${i.item_name} ×${i.quantity}`).join(', ') : '—'}
                    </td>
                    <td className="td font-semibold">₹{Number(order.total_amount).toLocaleString()}</td>
                    <td className="td"><StatusBadge status={order.status} /></td>
                    <td className="td text-xs text-gray-400">
                      {new Date(order.created_at).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}
                    </td>
                    <td className="td">
                      {nextStatus && (
                        <button onClick={() => updateMutation.mutate({ id: order.id, status: nextStatus })}
                          disabled={updateMutation.isPending}
                          className="btn-primary text-xs px-3 py-1.5">
                          {STATUS_LABEL[order.status]}
                        </button>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Create Order Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-6 border-b">
              <h2 className="text-lg font-semibold">New Order</h2>
              <button onClick={() => setShowForm(false)}><X className="w-5 h-5 text-gray-400" /></button>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Room</label>
                <select className="input" value={form.room_id} onChange={e => setForm({ ...form, room_id: e.target.value })}>
                  <option value="">Select room</option>
                  {rooms.filter(r => r.room_status === 'occupied').map(r => (
                    <option key={r.id} value={r.id}>Room {r.room_number}{r.guest_name ? ` – ${r.guest_name}` : ''}</option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Order Type</label>
                  <select className="input" value={form.order_type} onChange={e => setForm({ ...form, order_type: e.target.value })}>
                    {ORDER_TYPES.map(t => <option key={t} value={t} className="capitalize">{t}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Guest Name</label>
                  <input className="input" value={form.guest_name} onChange={e => setForm({ ...form, guest_name: e.target.value })} placeholder="Guest name" />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-medium text-gray-700">Items</label>
                  <button type="button" onClick={() => setForm({ ...form, items: [...form.items, { item_name: '', quantity: 1, unit_price: 0 }] })}
                    className="text-xs text-blue-600 hover:underline">+ Add Item</button>
                </div>
                <div className="space-y-2">
                  {form.items.map((item, idx) => (
                    <div key={idx} className="grid grid-cols-[1fr_80px_80px_auto] gap-2 items-center">
                      <input className="input text-sm" placeholder="Item name" value={item.item_name}
                        onChange={e => { const items = [...form.items]; items[idx].item_name = e.target.value; setForm({ ...form, items }) }} />
                      <input type="number" className="input text-sm" placeholder="Qty" min={1} value={item.quantity}
                        onChange={e => { const items = [...form.items]; items[idx].quantity = +e.target.value; setForm({ ...form, items }) }} />
                      <input type="number" className="input text-sm" placeholder="₹" min={0} value={item.unit_price}
                        onChange={e => { const items = [...form.items]; items[idx].unit_price = +e.target.value; setForm({ ...form, items }) }} />
                      {form.items.length > 1 && (
                        <button type="button" onClick={() => setForm({ ...form, items: form.items.filter((_, i) => i !== idx) })}>
                          <X className="w-4 h-4 text-gray-400" />
                        </button>
                      )}
                    </div>
                  ))}
                </div>
                <p className="text-right text-sm font-semibold text-gray-700 mt-2">
                  Total: ₹{form.items.reduce((s, i) => s + i.quantity * i.unit_price, 0).toLocaleString()}
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
                <textarea className="input resize-none" rows={2} value={form.notes}
                  onChange={e => setForm({ ...form, notes: e.target.value })} placeholder="Special instructions..." />
              </div>
            </div>
            <div className="flex gap-3 p-6 border-t">
              <button onClick={() => setShowForm(false)} className="btn-secondary flex-1">Cancel</button>
              <button onClick={handleCreate} disabled={createMutation.isPending || !form.room_id}
                className="btn-primary flex-1">
                {createMutation.isPending ? 'Placing...' : 'Place Order'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
