import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Trash2, Clock, Phone } from 'lucide-react'
import api from '@/lib/api'
import { Modal } from '@/components/ui/Modal'
import { PageLoader } from '@/components/ui/LoadingSpinner'
import toast from 'react-hot-toast'
import { useSelector } from 'react-redux'
import type { RootState } from '@/store'
import { useAdminPropertyId } from '@/hooks/useAdminPropertyId'
import { RequirePropertyScope } from '@/components/layout/RequirePropertyScope'

type Contact = { id: string; contact_type: string; value: string; label?: string; is_primary: boolean }
type Schedule = { day_of_week: number; open_time: string; close_time: string; is_closed: boolean }

const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

export function PropertySettingsPage() {
  const qc = useQueryClient()
  const user = useSelector((s: RootState) => s.auth.user)
  const { propertyId, enabled } = useAdminPropertyId()
  const canManage = user?.role === 'property_manager' || user?.role === 'super_admin'

  const [showContact, setShowContact] = useState(false)
  const [contactForm, setContactForm] = useState({ contact_type: 'phone', value: '', label: '', is_primary: false })
  const [schedules, setSchedules] = useState<Schedule[]>([])

  const { data: contacts = [], isLoading } = useQuery<Contact[]>({
    queryKey: ['property-contacts', propertyId],
    enabled,
    queryFn: () => api.get(`/contacts/properties/${propertyId}`).then(r => r.data),
  })

  const { data: loadedSchedules, isLoading: schedLoading } = useQuery<Schedule[]>({
    queryKey: ['property-schedules', propertyId],
    enabled,
    queryFn: () => api.get(`/properties/${propertyId}/schedules`).then(r => r.data),
  })

  useEffect(() => {
    if (loadedSchedules?.length) {
      setSchedules(loadedSchedules)
    } else if (propertyId && loadedSchedules && schedules.length === 0) {
      setSchedules(
        Array.from({ length: 7 }, (_, i) => ({
          day_of_week: i,
          open_time: '06:00:00',
          close_time: '23:00:00',
          is_closed: false,
        }))
      )
    }
  }, [loadedSchedules, propertyId])

  const addContact = useMutation({
    mutationFn: () => api.post(`/contacts/properties/${propertyId}`, contactForm),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['property-contacts'] })
      setShowContact(false)
      toast.success('Contact added')
    },
  })

  const deleteContact = useMutation({
    mutationFn: (id: string) => api.delete(`/contacts/properties/${propertyId}/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['property-contacts'] })
      toast.success('Contact removed')
    },
  })

  const saveSchedules = useMutation({
    mutationFn: () =>
      api.put(`/properties/${propertyId}/schedules`, {
        schedules: schedules.map(s => ({
          day_of_week: s.day_of_week,
          open_time: s.open_time.length === 5 ? `${s.open_time}:00` : s.open_time,
          close_time: s.close_time.length === 5 ? `${s.close_time}:00` : s.close_time,
          is_closed: s.is_closed,
        })),
      }),
    onSuccess: () => toast.success('Operating hours saved'),
  })

  if (isLoading || schedLoading) return <PageLoader />

  return (
    <RequirePropertyScope>
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Property Settings</h1>
          <p className="text-gray-500 text-sm">Contacts and weekly operating hours</p>
        </div>
      </div>

      <section className="card mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Phone className="w-5 h-5 text-blue-600" />
            Property contacts
          </h2>
          {canManage && (
            <button className="btn-primary text-sm" onClick={() => setShowContact(true)}>
              <Plus className="w-4 h-4 inline mr-1" />
              Add
            </button>
          )}
        </div>
        <ul className="divide-y divide-gray-100">
          {contacts.map(c => (
            <li key={c.id} className="py-3 flex justify-between items-center">
              <div>
                <span className="text-xs uppercase text-gray-400">{c.contact_type}</span>
                <p className="font-medium">{c.value}</p>
                {c.label && <p className="text-xs text-gray-500">{c.label}</p>}
              </div>
              {canManage && (
                <button className="text-red-600 hover:bg-red-50 p-2 rounded" onClick={() => deleteContact.mutate(c.id)}>
                  <Trash2 className="w-4 h-4" />
                </button>
              )}
            </li>
          ))}
          {contacts.length === 0 && <p className="text-gray-400 text-sm">No contacts yet.</p>}
        </ul>
      </section>

      <section className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Clock className="w-5 h-5 text-blue-600" />
            Operating schedule
          </h2>
          {canManage && (
            <button className="btn-primary text-sm" onClick={() => saveSchedules.mutate()} disabled={saveSchedules.isPending}>
              Save hours
            </button>
          )}
        </div>
        <div className="space-y-2">
          {schedules.map((s, idx) => (
            <div key={s.day_of_week} className="grid grid-cols-4 gap-3 items-center text-sm">
              <span className="font-medium">{DAYS[s.day_of_week]}</span>
              <label className="flex items-center gap-2 col-span-3">
                <input
                  type="checkbox"
                  checked={s.is_closed}
                  disabled={!canManage}
                  onChange={e => {
                    const next = [...schedules]
                    next[idx] = { ...s, is_closed: e.target.checked }
                    setSchedules(next)
                  }}
                />
                Closed
              </label>
              {!s.is_closed && (
                <>
                  <input
                    type="time"
                    className="input col-span-1"
                    disabled={!canManage}
                    value={s.open_time.slice(0, 5)}
                    onChange={e => {
                      const next = [...schedules]
                      next[idx] = { ...s, open_time: e.target.value }
                      setSchedules(next)
                    }}
                  />
                  <input
                    type="time"
                    className="input col-span-1"
                    disabled={!canManage}
                    value={s.close_time.slice(0, 5)}
                    onChange={e => {
                      const next = [...schedules]
                      next[idx] = { ...s, close_time: e.target.value }
                      setSchedules(next)
                    }}
                  />
                </>
              )}
            </div>
          ))}
        </div>
      </section>

      <Modal isOpen={showContact} onClose={() => setShowContact(false)} title="Add contact">
        <div className="space-y-3">
          <select className="input" value={contactForm.contact_type} onChange={e => setContactForm({ ...contactForm, contact_type: e.target.value })}>
            <option value="phone">Phone</option>
            <option value="email">Email</option>
          </select>
          <input className="input" placeholder="Value" value={contactForm.value} onChange={e => setContactForm({ ...contactForm, value: e.target.value })} />
          <input className="input" placeholder="Label (optional)" value={contactForm.label} onChange={e => setContactForm({ ...contactForm, label: e.target.value })} />
          <button className="btn-primary w-full" onClick={() => addContact.mutate()} disabled={!contactForm.value}>
            Save
          </button>
        </div>
      </Modal>
    </div>
    </RequirePropertyScope>
  )
}
