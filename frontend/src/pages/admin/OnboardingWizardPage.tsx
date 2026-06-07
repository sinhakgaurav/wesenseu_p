import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ChevronLeft, ChevronRight, Rocket, Upload } from 'lucide-react'
import api from '@/lib/api'
import { PageLoader } from '@/components/ui/LoadingSpinner'
import toast from 'react-hot-toast'
import { useSelector } from 'react-redux'
import type { RootState } from '@/store'
import { usePropertyScope } from '@/context/PropertyScopeContext'
import { RequirePropertyScope } from '@/components/layout/RequirePropertyScope'
import type { PropertyRoomCategory } from '@/lib/types'

type OnboardingSession = {
  id: string
  customer_id?: string
  property_id?: string
  current_step: string
  step_index: number
  payload: Record<string, unknown>
  status: string
}

type CatalogItem = { id: string; display_name: string; code: string }

const STEP_LABELS: Record<string, string> = {
  business: 'Business',
  property: 'Property',
  features: 'Features',
  room_categories: 'Room categories',
  rooms: 'Rooms',
  f_and_b: 'F&B',
  inventory: 'Inventory',
  employees: 'Employees',
  complete: 'Complete',
}

export function OnboardingWizardPage() {
  const qc = useQueryClient()
  const user = useSelector((s: RootState) => s.auth.user)
  const { effectivePropertyId } = usePropertyScope()
  const propertyId = effectivePropertyId || undefined
  const isSuperAdmin = user?.role === 'super_admin'

  const [sessionId, setSessionId] = useState<string | null>(null)
  const [business, setBusiness] = useState({ company_name: '', contact_email: '', contact_phone: '' })
  const [propertyForm, setPropertyForm] = useState({
    name: '',
    property_type: 'hotel',
    city: '',
    total_rooms: 0,
  })
  const [propertyPhone, setPropertyPhone] = useState('')
  const [selectedFeatures, setSelectedFeatures] = useState<string[]>([])

  const [categoryForm, setCategoryForm] = useState({ code: '', display_name: '', base_price: '' })
  const [bulkRooms, setBulkRooms] = useState({
    property_room_category_id: '',
    count: 10,
    start_number: 101,
    room_number_prefix: '',
    floor_number: 1,
  })
  const [fbForm, setFbForm] = useState({ outlet_name: 'Main Restaurant', outlet_type: 'restaurant' })
  const [menuItems, setMenuItems] = useState([{ name: 'Continental Breakfast', price: '450' }])
  const [inventoryNote, setInventoryNote] = useState('')

  const { data: steps = [], isLoading: stepsLoading } = useQuery<string[]>({
    queryKey: ['onboarding-steps'],
    queryFn: async () => {
      const { data } = await api.get('/onboarding/steps')
      return data
    },
  })

  const { data: featureCatalog = [] } = useQuery<CatalogItem[]>({
    queryKey: ['catalog-features'],
    queryFn: async () => {
      const { data } = await api.get('/catalog/items?kind=property_feature')
      return data
    },
  })

  const { data: session, isLoading: sessionLoading } = useQuery<OnboardingSession>({
    queryKey: ['onboarding-session', sessionId],
    enabled: !!sessionId,
    queryFn: async () => {
      const { data } = await api.get(`/onboarding/sessions/${sessionId}`)
      return data
    },
  })

  const activePropertyId = session?.property_id || propertyId

  const { data: categories = [] } = useQuery<PropertyRoomCategory[]>({
    queryKey: ['room-categories', activePropertyId],
    enabled: !!activePropertyId,
    queryFn: async () => {
      const { data } = await api.get(`/room-categories?property_id=${activePropertyId}`)
      return data
    },
  })

  useEffect(() => {
    if (session?.payload && typeof session.payload === 'object') {
      const p = session.payload as Record<string, string>
      if (p.company_name) setBusiness((b) => ({ ...b, company_name: p.company_name }))
      if (p.contact_email) setBusiness((b) => ({ ...b, contact_email: p.contact_email }))
      if (p.contact_phone) setBusiness((b) => ({ ...b, contact_phone: p.contact_phone }))
    }
  }, [session?.id, session?.payload])

  useEffect(() => {
    if (categories.length && !bulkRooms.property_room_category_id) {
      setBulkRooms((b) => ({ ...b, property_room_category_id: categories[0].id }))
    }
  }, [categories, bulkRooms.property_room_category_id])

  const startMutation = useMutation({
    mutationFn: async () => {
      const { data } = await api.post('/onboarding/sessions', {
        property_id: propertyId || undefined,
      })
      return data as OnboardingSession
    },
    onSuccess: (data) => {
      setSessionId(data.id)
      qc.setQueryData(['onboarding-session', data.id], data)
      toast.success('Onboarding session started')
    },
    onError: () => toast.error('Could not start session'),
  })

  const patchMutation = useMutation({
    mutationFn: async (body: Record<string, unknown>) => {
      if (!sessionId) throw new Error('No session')
      const { data } = await api.patch(`/onboarding/sessions/${sessionId}`, body)
      return data as OnboardingSession
    },
    onSuccess: (data) => {
      qc.setQueryData(['onboarding-session', sessionId], data)
    },
    onError: () => toast.error('Save failed'),
  })

  const importEmployeesMutation = useMutation({
    mutationFn: async (file: File) => {
      const form = new FormData()
      form.append('file', file)
      const params = activePropertyId ? `?property_id=${activePropertyId}` : ''
      const { data } = await api.post(`/employees/import${params}`, form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      return data
    },
    onSuccess: (data: { created: number; updated: number }) => {
      toast.success(`Employees: ${data.created} created, ${data.updated} updated`)
    },
    onError: () => toast.error('Employee import failed'),
  })

  const currentStep = session?.current_step || 'business'
  const stepIndex = session?.step_index ?? 0

  const goNext = async () => {
    if (!session || !steps.length) return
    const patch: Record<string, unknown> = {}
    const pid = activePropertyId

    if (currentStep === 'business') {
      patch.payload_patch = { ...business }
      if (business.contact_email && session.customer_id) {
        try {
          await api.post(`/contacts/customers/${session.customer_id}`, {
            contact_type: 'email',
            value: business.contact_email,
            label: 'Primary',
            is_primary: true,
          })
        } catch {
          /* may exist */
        }
      }
    }

    if (currentStep === 'property') {
      if (isSuperAdmin && propertyForm.name.trim()) {
        try {
          const { data: prop } = await api.post('/properties', {
            ...propertyForm,
            customer_id: session.customer_id,
          })
          patch.property_id = prop.id
          if (propertyPhone.trim()) {
            await api.post(`/contacts/properties/${prop.id}`, {
              contact_type: 'phone',
              value: propertyPhone.trim(),
              label: 'Front desk',
              is_primary: true,
            })
          }
        } catch {
          toast.error('Property create failed (super_admin only)')
          return
        }
      } else if (pid) {
        patch.property_id = pid
        patch.payload_patch = { property: propertyForm }
        if (propertyPhone.trim()) {
          try {
            await api.post(`/contacts/properties/${pid}`, {
              contact_type: 'phone',
              value: propertyPhone.trim(),
              label: 'Front desk',
              is_primary: true,
            })
          } catch {
            /* */
          }
        }
      }
    }

    if (currentStep === 'features' && pid && selectedFeatures.length) {
      await api.put(`/catalog/properties/${pid}/features`, {
        catalog_item_ids: selectedFeatures,
      })
    }

    if (currentStep === 'room_categories' && pid && categoryForm.display_name.trim()) {
      await api.post('/room-categories', {
        property_id: pid,
        code: categoryForm.code.trim() || categoryForm.display_name.toLowerCase().replace(/\s+/g, '_'),
        display_name: categoryForm.display_name.trim(),
        base_price: categoryForm.base_price ? Number(categoryForm.base_price) : undefined,
      })
      qc.invalidateQueries({ queryKey: ['room-categories'] })
    }

    if (currentStep === 'rooms' && pid && bulkRooms.property_room_category_id) {
      const { data } = await api.post('/rooms/bulk', {
        property_id: pid,
        property_room_category_id: bulkRooms.property_room_category_id,
        count: bulkRooms.count,
        start_number: bulkRooms.start_number,
        room_number_prefix: bulkRooms.room_number_prefix,
        floor_number: bulkRooms.floor_number,
      })
      patch.payload_patch = { rooms_created: (data as unknown[]).length }
      toast.success(`Created ${(data as unknown[]).length} rooms`)
    }

    if (currentStep === 'f_and_b' && pid && fbForm.outlet_name.trim()) {
      const { data: outlet } = await api.post(`/fb/properties/${pid}/outlets`, {
        property_id: pid,
        name: fbForm.outlet_name.trim(),
        outlet_type: fbForm.outlet_type,
      })
      for (const item of menuItems) {
        if (!item.name.trim()) continue
        await api.post(`/fb/outlets/${outlet.id}/menu`, {
          name: item.name.trim(),
          price: Number(item.price) || 0,
        })
      }
      toast.success('F&B outlet and menu saved')
    }

    if (currentStep === 'inventory' && pid && inventoryNote.trim()) {
      patch.payload_patch = { inventory_note: inventoryNote }
    }

    const nextIndex = Math.min(stepIndex + 1, steps.length - 1)
    const nextStep = steps[nextIndex]
    patch.current_step = nextStep
    patch.step_index = nextIndex
    if (nextStep === 'complete') patch.status = 'completed'

    await patchMutation.mutateAsync(patch)
    toast.success('Step saved')
  }

  const goBack = () => {
    if (!session || stepIndex <= 0) return
    patchMutation.mutate({
      current_step: steps[stepIndex - 1],
      step_index: stepIndex - 1,
    })
  }

  if (stepsLoading) return <PageLoader />

  return (
    <RequirePropertyScope>
    <div className="max-w-3xl mx-auto">
      <div className="page-header mb-6">
        <div>
          <h1 className="page-title flex items-center gap-2">
            <Rocket className="w-7 h-7 text-blue-600" />
            Property onboarding
          </h1>
          <p className="text-gray-500 text-sm">Guided setup for business, property, rooms, F&B, and staff</p>
        </div>
        {!sessionId && (
          <button type="button" className="btn-primary" disabled={startMutation.isPending} onClick={() => startMutation.mutate()}>
            Start wizard
          </button>
        )}
      </div>

      {sessionId && (
        <>
          <div className="flex flex-wrap gap-2 mb-6">
            {steps.map((s, i) => (
              <span
                key={s}
                className={`text-xs px-2 py-1 rounded-full ${
                  i === stepIndex ? 'bg-blue-600 text-white' : i < stepIndex ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-500'
                }`}
              >
                {STEP_LABELS[s] || s}
              </span>
            ))}
          </div>

          {sessionLoading ? (
            <PageLoader />
          ) : (
            <div className="bg-white rounded-xl border border-gray-100 p-6 space-y-4">
              <h2 className="text-lg font-semibold">{STEP_LABELS[currentStep] || currentStep}</h2>

              {currentStep === 'business' && (
                <div className="space-y-3">
                  <input className="input w-full" placeholder="Company / business name" value={business.company_name} onChange={(e) => setBusiness({ ...business, company_name: e.target.value })} />
                  <input className="input w-full" type="email" placeholder="Primary email" value={business.contact_email} onChange={(e) => setBusiness({ ...business, contact_email: e.target.value })} />
                  <input className="input w-full" placeholder="Primary phone" value={business.contact_phone} onChange={(e) => setBusiness({ ...business, contact_phone: e.target.value })} />
                </div>
              )}

              {currentStep === 'property' && (
                <div className="space-y-3">
                  {!isSuperAdmin && (
                    <p className="text-sm text-amber-700 bg-amber-50 p-3 rounded-lg">
                      Using property {activePropertyId || '—'}. Super admins can create a new property here.
                    </p>
                  )}
                  <input className="input w-full" placeholder="Property name" value={propertyForm.name} onChange={(e) => setPropertyForm({ ...propertyForm, name: e.target.value })} />
                  <select className="input w-full" value={propertyForm.property_type} onChange={(e) => setPropertyForm({ ...propertyForm, property_type: e.target.value })}>
                    {['hotel', 'resort', 'serviced_apartment', 'hostel'].map((t) => (
                      <option key={t} value={t}>{t.replace(/_/g, ' ')}</option>
                    ))}
                  </select>
                  <input className="input w-full" placeholder="City" value={propertyForm.city} onChange={(e) => setPropertyForm({ ...propertyForm, city: e.target.value })} />
                  <input className="input w-full" type="number" min={0} placeholder="Total rooms (planned)" value={propertyForm.total_rooms} onChange={(e) => setPropertyForm({ ...propertyForm, total_rooms: Number(e.target.value) })} />
                  <input className="input w-full" placeholder="Property contact phone" value={propertyPhone} onChange={(e) => setPropertyPhone(e.target.value)} />
                </div>
              )}

              {currentStep === 'features' && (
                <div className="grid grid-cols-2 gap-2 max-h-64 overflow-y-auto">
                  {featureCatalog.map((f) => (
                    <label key={f.id} className="flex items-center gap-2 text-sm p-2 border rounded-lg cursor-pointer hover:bg-gray-50">
                      <input type="checkbox" checked={selectedFeatures.includes(f.id)} onChange={(e) => setSelectedFeatures((prev) => (e.target.checked ? [...prev, f.id] : prev.filter((id) => id !== f.id)))} />
                      {f.display_name}
                    </label>
                  ))}
                </div>
              )}

              {currentStep === 'room_categories' && (
                <div className="space-y-3">
                  {categories.length > 0 && (
                    <p className="text-sm text-gray-600">Existing: {categories.map((c) => c.display_name).join(', ')}</p>
                  )}
                  <input className="input w-full" placeholder="Category code (optional)" value={categoryForm.code} onChange={(e) => setCategoryForm({ ...categoryForm, code: e.target.value })} />
                  <input className="input w-full" placeholder="Display name (e.g. Deluxe)" value={categoryForm.display_name} onChange={(e) => setCategoryForm({ ...categoryForm, display_name: e.target.value })} />
                  <input className="input w-full" type="number" placeholder="Base price (₹)" value={categoryForm.base_price} onChange={(e) => setCategoryForm({ ...categoryForm, base_price: e.target.value })} />
                </div>
              )}

              {currentStep === 'rooms' && (
                <div className="space-y-3">
                  {!activePropertyId && <p className="text-amber-700 text-sm">Complete the Property step first.</p>}
                  <select className="input w-full" value={bulkRooms.property_room_category_id} onChange={(e) => setBulkRooms({ ...bulkRooms, property_room_category_id: e.target.value })}>
                    <option value="">Select category</option>
                    {categories.map((c) => (
                      <option key={c.id} value={c.id}>{c.display_name}</option>
                    ))}
                  </select>
                  <div className="grid grid-cols-2 gap-3">
                    <input className="input" type="number" min={1} placeholder="Count" value={bulkRooms.count} onChange={(e) => setBulkRooms({ ...bulkRooms, count: Number(e.target.value) })} />
                    <input className="input" type="number" placeholder="Start room #" value={bulkRooms.start_number} onChange={(e) => setBulkRooms({ ...bulkRooms, start_number: Number(e.target.value) })} />
                    <input className="input" placeholder="Prefix (e.g. 2-)" value={bulkRooms.room_number_prefix} onChange={(e) => setBulkRooms({ ...bulkRooms, room_number_prefix: e.target.value })} />
                    <input className="input" type="number" placeholder="Floor" value={bulkRooms.floor_number} onChange={(e) => setBulkRooms({ ...bulkRooms, floor_number: Number(e.target.value) })} />
                  </div>
                </div>
              )}

              {currentStep === 'f_and_b' && (
                <div className="space-y-3">
                  <input className="input w-full" placeholder="Outlet name" value={fbForm.outlet_name} onChange={(e) => setFbForm({ ...fbForm, outlet_name: e.target.value })} />
                  <select className="input w-full" value={fbForm.outlet_type} onChange={(e) => setFbForm({ ...fbForm, outlet_type: e.target.value })}>
                    {['restaurant', 'kitchen', 'bar', 'room_service'].map((t) => (
                      <option key={t} value={t}>{t.replace(/_/g, ' ')}</option>
                    ))}
                  </select>
                  <p className="text-sm font-medium text-gray-700">Menu items</p>
                  {menuItems.map((item, idx) => (
                    <div key={idx} className="flex gap-2">
                      <input className="input flex-1" placeholder="Dish name" value={item.name} onChange={(e) => {
                        const next = [...menuItems]
                        next[idx] = { ...next[idx], name: e.target.value }
                        setMenuItems(next)
                      }} />
                      <input className="input w-24" placeholder="₹" value={item.price} onChange={(e) => {
                        const next = [...menuItems]
                        next[idx] = { ...next[idx], price: e.target.value }
                        setMenuItems(next)
                      }} />
                    </div>
                  ))}
                  <button type="button" className="text-sm text-blue-600" onClick={() => setMenuItems([...menuItems, { name: '', price: '' }])}>
                    + Add dish
                  </button>
                </div>
              )}

              {currentStep === 'inventory' && (
                <div className="space-y-3">
                  <p className="text-sm text-gray-600">
                    Stock items are managed under Inventory. Add a note for your team or open Inventory after onboarding.
                  </p>
                  <textarea className="input w-full resize-none" rows={3} placeholder="Notes (optional)" value={inventoryNote} onChange={(e) => setInventoryNote(e.target.value)} />
                  <a href="/admin/inventory" className="text-sm text-blue-600 hover:underline">Open Inventory →</a>
                </div>
              )}

              {currentStep === 'employees' && (
                <div className="space-y-3">
                  <p className="text-sm text-gray-600">Upload a CSV to bulk-add staff (same format as Employees page).</p>
                  <label className="btn-secondary inline-flex items-center gap-2 cursor-pointer">
                    <Upload className="w-4 h-4" />
                    Import employees CSV
                    <input
                      type="file"
                      accept=".csv"
                      className="hidden"
                      onChange={(e) => {
                        const f = e.target.files?.[0]
                        if (f) importEmployeesMutation.mutate(f)
                        e.target.value = ''
                      }}
                    />
                  </label>
                  <a href="/admin/employees" className="block text-sm text-blue-600 hover:underline">Open Employees →</a>
                </div>
              )}

              {currentStep === 'complete' && (
                <p className="text-green-700 font-medium">Onboarding complete. You can use Dashboard, Rooms, Tasks, and Guests.</p>
              )}

              <div className="flex justify-between pt-4 border-t">
                <button type="button" className="btn-secondary flex items-center gap-1" disabled={stepIndex === 0 || patchMutation.isPending} onClick={goBack}>
                  <ChevronLeft className="w-4 h-4" />
                  Back
                </button>
                {currentStep !== 'complete' && (
                  <button type="button" className="btn-primary flex items-center gap-1" disabled={patchMutation.isPending} onClick={() => goNext()}>
                    {patchMutation.isPending ? 'Saving…' : 'Save & continue'}
                    <ChevronRight className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>
          )}
        </>
      )}
    </div>
    </RequirePropertyScope>
  )
}
