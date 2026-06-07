import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, UtensilsCrossed, Trash2, Pencil } from 'lucide-react'
import api from '@/lib/api'
import { Modal } from '@/components/ui/Modal'
import { PageLoader } from '@/components/ui/LoadingSpinner'
import toast from 'react-hot-toast'
import { useSelector } from 'react-redux'
import type { RootState } from '@/store'
import { useAdminPropertyId } from '@/hooks/useAdminPropertyId'
import { RequirePropertyScope } from '@/components/layout/RequirePropertyScope'

type Outlet = { id: string; name: string; outlet_type: string }
type MenuItem = { id: string; name: string; price: number; is_available?: boolean }

export function FnBPage() {
  const qc = useQueryClient()
  const user = useSelector((s: RootState) => s.auth.user)
  const { propertyId, enabled } = useAdminPropertyId()
  const canManage = user?.role === 'property_manager' || user?.role === 'super_admin'

  const [selectedOutlet, setSelectedOutlet] = useState<Outlet | null>(null)
  const [showOutlet, setShowOutlet] = useState(false)
  const [outletForm, setOutletForm] = useState({ name: '', outlet_type: 'restaurant' })
  const [showMenu, setShowMenu] = useState(false)
  const [menuForm, setMenuForm] = useState({ name: '', price: '' })

  const { data: outlets = [], isLoading } = useQuery<Outlet[]>({
    queryKey: ['fb-outlets', propertyId],
    enabled,
    queryFn: () => api.get(`/fb/properties/${propertyId}/outlets`).then(r => r.data),
  })

  const { data: menu = [] } = useQuery<MenuItem[]>({
    queryKey: ['fb-menu', selectedOutlet?.id],
    enabled: !!selectedOutlet?.id,
    queryFn: () => api.get(`/fb/outlets/${selectedOutlet!.id}/menu`).then(r => r.data),
  })

  const createOutlet = useMutation({
    mutationFn: () => api.post(`/fb/properties/${propertyId}/outlets`, { property_id: propertyId, ...outletForm }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['fb-outlets'] })
      setShowOutlet(false)
      toast.success('Outlet created')
    },
  })

  const deleteOutlet = useMutation({
    mutationFn: (id: string) => api.delete(`/fb/outlets/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['fb-outlets'] })
      setSelectedOutlet(null)
      toast.success('Outlet removed')
    },
  })

  const addMenu = useMutation({
    mutationFn: () =>
      api.post(`/fb/outlets/${selectedOutlet!.id}/menu`, {
        name: menuForm.name,
        price: Number(menuForm.price),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['fb-menu'] })
      setShowMenu(false)
      setMenuForm({ name: '', price: '' })
      toast.success('Menu item added')
    },
  })

  const deleteMenu = useMutation({
    mutationFn: (id: string) => api.delete(`/fb/menu/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['fb-menu'] })
      toast.success('Menu item removed')
    },
  })

  if (isLoading) return <PageLoader />

  return (
    <RequirePropertyScope>
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Food & Beverage</h1>
          <p className="text-gray-500 text-sm">Outlets and menus for this property</p>
        </div>
        {canManage && (
          <button className="btn-primary flex items-center gap-2" onClick={() => setShowOutlet(true)}>
            <Plus className="w-4 h-4" />
            Add outlet
          </button>
        )}
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="card lg:col-span-1">
          <h2 className="font-semibold mb-3 flex items-center gap-2">
            <UtensilsCrossed className="w-4 h-4" />
            Outlets
          </h2>
          <ul className="space-y-2">
            {outlets.map(o => (
              <li key={o.id}>
                <button
                  type="button"
                  onClick={() => setSelectedOutlet(o)}
                  className={`w-full text-left px-3 py-2 rounded-lg border ${
                    selectedOutlet?.id === o.id ? 'border-blue-500 bg-blue-50' : 'border-gray-100 hover:bg-gray-50'
                  }`}
                >
                  <p className="font-medium">{o.name}</p>
                  <p className="text-xs text-gray-500 capitalize">{o.outlet_type}</p>
                </button>
              </li>
            ))}
            {outlets.length === 0 && <p className="text-sm text-gray-400">No outlets yet.</p>}
          </ul>
          {selectedOutlet && canManage && (
            <button className="mt-3 text-sm text-red-600" onClick={() => deleteOutlet.mutate(selectedOutlet.id)}>
              <Trash2 className="w-4 h-4 inline" /> Remove outlet
            </button>
          )}
        </div>

        <div className="card lg:col-span-2">
          {selectedOutlet ? (
            <>
              <div className="flex justify-between items-center mb-4">
                <h2 className="font-semibold">{selectedOutlet.name} — Menu</h2>
                {canManage && (
                  <button className="btn-primary text-sm" onClick={() => setShowMenu(true)}>
                    <Plus className="w-4 h-4 inline" /> Add item
                  </button>
                )}
              </div>
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-gray-500 border-b">
                    <th className="pb-2">Item</th>
                    <th className="pb-2">Price (₹)</th>
                    {canManage && <th className="pb-2" />}
                  </tr>
                </thead>
                <tbody>
                  {menu.map(m => (
                    <tr key={m.id} className="border-b border-gray-50">
                      <td className="py-2">{m.name}</td>
                      <td className="py-2">{m.price}</td>
                      {canManage && (
                        <td className="py-2 text-right">
                          <button className="text-red-600" onClick={() => deleteMenu.mutate(m.id)}>
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          ) : (
            <p className="text-gray-400">Select an outlet to manage its menu.</p>
          )}
        </div>
      </div>

      <Modal isOpen={showOutlet} onClose={() => setShowOutlet(false)} title="New outlet">
        <div className="space-y-3">
          <input className="input" placeholder="Name" value={outletForm.name} onChange={e => setOutletForm({ ...outletForm, name: e.target.value })} />
          <select className="input" value={outletForm.outlet_type} onChange={e => setOutletForm({ ...outletForm, outlet_type: e.target.value })}>
            {['restaurant', 'bar', 'cafe', 'room_service', 'banquet'].map(t => (
              <option key={t} value={t}>{t.replace(/_/g, ' ')}</option>
            ))}
          </select>
          <button className="btn-primary w-full" disabled={!outletForm.name} onClick={() => createOutlet.mutate()}>
            Create
          </button>
        </div>
      </Modal>

      <Modal isOpen={showMenu} onClose={() => setShowMenu(false)} title="Add menu item">
        <div className="space-y-3">
          <input className="input" placeholder="Dish name" value={menuForm.name} onChange={e => setMenuForm({ ...menuForm, name: e.target.value })} />
          <input className="input" type="number" placeholder="Price" value={menuForm.price} onChange={e => setMenuForm({ ...menuForm, price: e.target.value })} />
          <button className="btn-primary w-full" disabled={!menuForm.name || !menuForm.price} onClick={() => addMenu.mutate()}>
            Add
          </button>
        </div>
      </Modal>
    </div>
    </RequirePropertyScope>
  )
}
