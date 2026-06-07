import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Pencil, Trash2 } from 'lucide-react'
import api from '@/lib/api'
import toast from 'react-hot-toast'

type Plan = {
  id: string
  name: string
  slug: string
  tagline?: string
  price_monthly?: number
  price_yearly?: number
  currency: string
  room_limit?: number
  employee_limit?: number
  features: string[]
  is_active: boolean
  is_popular: boolean
  display_order: number
  cta_text: string
}

const emptyPlan = {
  name: '',
  slug: '',
  tagline: '',
  price_monthly: '',
  price_yearly: '',
  currency: 'INR',
  room_limit: '',
  employee_limit: '',
  features: '',
  cta_text: 'Get Started',
  is_popular: false,
  display_order: 0,
}

export function SuperAdminPlansTab() {
  const qc = useQueryClient()
  const [editing, setEditing] = useState<Plan | null>(null)
  const [form, setForm] = useState(emptyPlan)
  const [showForm, setShowForm] = useState(false)

  const { data: plans = [], isLoading } = useQuery<Plan[]>({
    queryKey: ['admin-plans'],
    queryFn: () => api.get('/plans?include_inactive=true').then((r) => r.data),
  })

  const savePlan = useMutation({
    mutationFn: async () => {
      const payload = {
        name: form.name,
        slug: form.slug,
        tagline: form.tagline || undefined,
        price_monthly: form.price_monthly ? Number(form.price_monthly) : null,
        price_yearly: form.price_yearly ? Number(form.price_yearly) : null,
        currency: form.currency,
        room_limit: form.room_limit ? Number(form.room_limit) : null,
        employee_limit: form.employee_limit ? Number(form.employee_limit) : null,
        features: form.features.split('\n').map((s) => s.trim()).filter(Boolean),
        cta_text: form.cta_text,
        is_popular: form.is_popular,
        display_order: Number(form.display_order) || 0,
        is_active: true,
      }
      if (editing) {
        return api.patch(`/plans/${editing.id}`, payload)
      }
      return api.post('/plans', payload)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin-plans'] })
      toast.success(editing ? 'Plan updated' : 'Plan created')
      setShowForm(false)
      setEditing(null)
      setForm(emptyPlan)
    },
    onError: () => toast.error('Failed to save plan'),
  })

  const deactivatePlan = useMutation({
    mutationFn: (id: string) => api.delete(`/plans/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin-plans'] })
      toast.success('Plan deactivated')
    },
  })

  const seedPlans = useMutation({
    mutationFn: () => api.post('/plans/seed'),
    onSuccess: (r) => {
      qc.invalidateQueries({ queryKey: ['admin-plans'] })
      toast.success(r.data.message || 'Plans seeded')
    },
  })

  function startEdit(p: Plan) {
    setEditing(p)
    setForm({
      name: p.name,
      slug: p.slug,
      tagline: p.tagline || '',
      price_monthly: p.price_monthly?.toString() || '',
      price_yearly: p.price_yearly?.toString() || '',
      currency: p.currency,
      room_limit: p.room_limit?.toString() || '',
      employee_limit: p.employee_limit?.toString() || '',
      features: (p.features || []).join('\n'),
      cta_text: p.cta_text,
      is_popular: p.is_popular,
      display_order: p.display_order,
    })
    setShowForm(true)
  }

  if (isLoading) return <p className="text-gray-400 text-sm">Loading plans…</p>

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        <button type="button" className="btn-primary text-sm" onClick={() => { setEditing(null); setForm(emptyPlan); setShowForm(true) }}>
          <Plus className="w-4 h-4 inline mr-1" /> New plan
        </button>
        <button type="button" className="btn-secondary text-sm" onClick={() => seedPlans.mutate()}>
          Seed default plans
        </button>
      </div>

      {showForm && (
        <div className="card grid grid-cols-1 md:grid-cols-2 gap-3">
          <input className="input" placeholder="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <input className="input" placeholder="Slug" value={form.slug} onChange={(e) => setForm({ ...form, slug: e.target.value })} />
          <input className="input md:col-span-2" placeholder="Tagline" value={form.tagline} onChange={(e) => setForm({ ...form, tagline: e.target.value })} />
          <input className="input" placeholder="Monthly price (INR)" value={form.price_monthly} onChange={(e) => setForm({ ...form, price_monthly: e.target.value })} />
          <input className="input" placeholder="Yearly price" value={form.price_yearly} onChange={(e) => setForm({ ...form, price_yearly: e.target.value })} />
          <textarea className="input md:col-span-2" rows={4} placeholder="Features (one per line)" value={form.features} onChange={(e) => setForm({ ...form, features: e.target.value })} />
          <div className="md:col-span-2 flex gap-2">
            <button type="button" className="btn-primary" onClick={() => savePlan.mutate()} disabled={savePlan.isPending}>
              {editing ? 'Update' : 'Create'}
            </button>
            <button type="button" className="btn-secondary" onClick={() => setShowForm(false)}>Cancel</button>
          </div>
        </div>
      )}

      <div className="space-y-2">
        {plans.map((p) => (
          <div key={p.id} className="card flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-900">{p.name} <span className="text-gray-400 font-normal">({p.slug})</span></p>
              <p className="text-xs text-gray-500">
                ₹{p.price_monthly?.toLocaleString() || 'Custom'}/mo · {p.is_active ? 'active' : 'inactive'}
                {p.is_popular && ' · popular'}
              </p>
            </div>
            <div className="flex gap-2">
              <button type="button" className="p-2 hover:bg-gray-100 rounded" onClick={() => startEdit(p)}><Pencil className="w-4 h-4" /></button>
              {p.is_active && (
                <button type="button" className="p-2 hover:bg-red-50 rounded text-red-600" onClick={() => deactivatePlan.mutate(p.id)}>
                  <Trash2 className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
