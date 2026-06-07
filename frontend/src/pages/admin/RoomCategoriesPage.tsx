import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Pencil, Trash2, Tags } from 'lucide-react'
import api from '@/lib/api'
import type { PropertyRoomCategory } from '@/lib/types'
import { Modal } from '@/components/ui/Modal'
import { PageLoader } from '@/components/ui/LoadingSpinner'
import toast from 'react-hot-toast'
import { useSelector } from 'react-redux'
import type { RootState } from '@/store'
import { useAdminPropertyId } from '@/hooks/useAdminPropertyId'
import { RequirePropertyScope } from '@/components/layout/RequirePropertyScope'

export function RoomCategoriesPage() {
  const qc = useQueryClient()
  const user = useSelector((s: RootState) => s.auth.user)
  const { propertyId, enabled } = useAdminPropertyId()
  const canManage = user?.role === 'super_admin' || user?.role === 'property_manager'

  const [showModal, setShowModal] = useState(false)
  const [editing, setEditing] = useState<PropertyRoomCategory | null>(null)
  const [form, setForm] = useState({ code: '', display_name: '', description: '', sort_order: 0 })
  const [amenitiesCat, setAmenitiesCat] = useState<PropertyRoomCategory | null>(null)
  const [selectedAmenityIds, setSelectedAmenityIds] = useState<string[]>([])

  const { data: availability = [] } = useQuery<{ category_name: string; vacant: number; occupied: number }[]>({
    queryKey: ['category-availability', propertyId],
    enabled,
    queryFn: () => api.get(`/room-categories/availability?property_id=${propertyId}`).then(r => r.data),
  })

  const { data: amenityCatalog = [] } = useQuery<{ id: string; display_name: string }[]>({
    queryKey: ['catalog-amenities'],
    queryFn: () => api.get('/catalog/items?kind=amenity').then(r => r.data),
  })

  const saveAmenities = useMutation({
    mutationFn: () =>
      api.put(`/catalog/room-categories/${amenitiesCat!.id}/amenities`, { catalog_item_ids: selectedAmenityIds }),
    onSuccess: () => {
      toast.success('Amenities saved')
      setAmenitiesCat(null)
    },
  })

  const openAmenities = async (c: PropertyRoomCategory) => {
    setAmenitiesCat(c)
    try {
      const { data } = await api.get(`/catalog/room-categories/${c.id}/amenities`)
      setSelectedAmenityIds((data as { id: string }[]).map(x => x.id))
    } catch {
      setSelectedAmenityIds([])
    }
  }

  const { data: categories = [], isLoading } = useQuery<PropertyRoomCategory[]>({
    queryKey: ['room-categories', propertyId],
    enabled,
    queryFn: async () => {
      const { data } = await api.get(`/room-categories?property_id=${propertyId}&include_inactive=true`)
      return data
    },
  })

  const saveMutation = useMutation({
    mutationFn: async () => {
      if (!propertyId) throw new Error('No property')
      if (editing) {
        await api.patch(`/room-categories/${editing.id}`, {
          display_name: form.display_name,
          description: form.description || undefined,
          sort_order: form.sort_order,
        })
      } else {
        await api.post('/room-categories', {
          property_id: propertyId,
          code: form.code.trim().toLowerCase().replace(/\s+/g, '_'),
          display_name: form.display_name.trim(),
          description: form.description || undefined,
          sort_order: form.sort_order,
        })
      }
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['room-categories'] })
      qc.invalidateQueries({ queryKey: ['benchmark-categories'] })
      setShowModal(false)
      setEditing(null)
      toast.success(editing ? 'Category updated' : 'Category created')
    },
    onError: () => toast.error('Save failed'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/room-categories/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['room-categories'] })
      qc.invalidateQueries({ queryKey: ['benchmark-categories'] })
      toast.success('Category deactivated')
    },
  })

  const openCreate = () => {
    setEditing(null)
    setForm({ code: '', display_name: '', description: '', sort_order: categories.length })
    setShowModal(true)
  }

  const openEdit = (c: PropertyRoomCategory) => {
    setEditing(c)
    setForm({
      code: c.code,
      display_name: c.display_name,
      description: c.description || '',
      sort_order: c.sort_order,
    })
    setShowModal(true)
  }

  if (isLoading) return <PageLoader />

  return (
    <RequirePropertyScope>
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title flex items-center gap-2">
            <Tags className="w-7 h-7 text-blue-600" />
            Room categories
          </h1>
          <p className="text-gray-500 text-sm">
            CRUD for room types on this property. Rooms and benchmarks use these definitions.
          </p>
        </div>
        {canManage && (
          <button type="button" onClick={openCreate} className="btn-primary flex items-center gap-2">
            <Plus className="w-4 h-4" />
            Add category
          </button>
        )}
      </div>

      {availability.length > 0 && (
        <div className="card mb-4 grid sm:grid-cols-3 gap-3 text-sm">
          {availability.map(a => (
            <div key={a.category_name} className="p-3 bg-gray-50 rounded-lg">
              <p className="font-medium">{a.category_name}</p>
              <p className="text-gray-500">Vacant {a.vacant} · Occupied {a.occupied}</p>
            </div>
          ))}
        </div>
      )}

      <div className="card overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="text-left p-3 font-medium text-gray-600">Code</th>
              <th className="text-left p-3 font-medium text-gray-600">Display name</th>
              <th className="text-left p-3 font-medium text-gray-600">Sort</th>
              <th className="text-left p-3 font-medium text-gray-600">Active</th>
              {canManage && <th className="text-right p-3 font-medium text-gray-600">Actions</th>}
            </tr>
          </thead>
          <tbody>
            {categories.map((c) => (
              <tr key={c.id} className="border-b border-gray-100 hover:bg-gray-50/80">
                <td className="p-3 font-mono text-xs">{c.code}</td>
                <td className="p-3 font-medium text-gray-900">{c.display_name}</td>
                <td className="p-3 text-gray-600">{c.sort_order}</td>
                <td className="p-3">{c.is_active ? 'Yes' : 'No'}</td>
                {canManage && (
                  <td className="p-3 text-right space-x-2">
                    <button
                      type="button"
                      onClick={() => openEdit(c)}
                      className="p-1.5 rounded-lg text-blue-600 hover:bg-blue-50 inline-flex"
                      title="Edit"
                    >
                      <Pencil className="w-4 h-4" />
                    </button>
                    <button
                      type="button"
                      onClick={() => openAmenities(c)}
                      className="p-1.5 rounded-lg text-indigo-600 hover:bg-indigo-50 inline-flex text-xs"
                      title="Amenities"
                    >
                      Amenities
                    </button>
                    {c.is_active && (
                      <button
                        type="button"
                        onClick={() => {
                          if (confirm(`Deactivate category "${c.display_name}"?`)) deleteMutation.mutate(c.id)
                        }}
                        className="p-1.5 rounded-lg text-red-500 hover:bg-red-50 inline-flex"
                        title="Deactivate"
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
        {categories.length === 0 && (
          <p className="p-8 text-center text-gray-500">No categories yet. Add one to drive room types and benchmarks.</p>
        )}
      </div>

      <Modal
        isOpen={showModal}
        onClose={() => { setShowModal(false); setEditing(null) }}
        title={editing ? 'Edit room category' : 'New room category'}
      >
        <div className="space-y-3">
          {!editing && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Code (slug)</label>
              <input
                className="input"
                value={form.code}
                onChange={(e) => setForm({ ...form, code: e.target.value })}
                placeholder="e.g. deluxe_suite"
              />
            </div>
          )}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Display name</label>
            <input
              className="input"
              value={form.display_name}
              onChange={(e) => setForm({ ...form, display_name: e.target.value })}
              placeholder="e.g. Deluxe Suite"
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
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Sort order</label>
            <input
              type="number"
              className="input"
              value={form.sort_order}
              onChange={(e) => setForm({ ...form, sort_order: Number(e.target.value) })}
            />
          </div>
          <div className="flex gap-2 pt-2">
            <button type="button" className="btn-secondary flex-1" onClick={() => setShowModal(false)}>
              Cancel
            </button>
            <button
              type="button"
              className="btn-primary flex-1"
              disabled={saveMutation.isPending || !form.display_name.trim() || (!editing && !form.code.trim())}
              onClick={() => saveMutation.mutate()}
            >
              {saveMutation.isPending ? 'Saving…' : 'Save'}
            </button>
          </div>
        </div>
      </Modal>

      <Modal isOpen={!!amenitiesCat} onClose={() => setAmenitiesCat(null)} title={`Amenities — ${amenitiesCat?.display_name}`}>
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {amenityCatalog.map(a => (
            <label key={a.id} className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={selectedAmenityIds.includes(a.id)}
                onChange={e => {
                  if (e.target.checked) setSelectedAmenityIds(ids => [...ids, a.id])
                  else setSelectedAmenityIds(ids => ids.filter(x => x !== a.id))
                }}
              />
              {a.display_name}
            </label>
          ))}
        </div>
        <button type="button" className="btn-primary w-full mt-4" onClick={() => saveAmenities.mutate()}>
          Save amenities
        </button>
      </Modal>
    </div>
    </RequirePropertyScope>
  )
}
