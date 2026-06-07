import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Building2, ChevronDown, ChevronRight, ExternalLink } from 'lucide-react'
import api from '@/lib/api'
import { Badge } from '@/components/ui/Badge'
import toast from 'react-hot-toast'

type HierarchyProperty = {
  id: string
  name: string
  subscription_status: string
  approval?: { id: string; status: string; requested_plan?: string } | null
}

type HierarchyCustomer = {
  id: string
  company_name: string
  email: string
  subscription_status: string
  is_active: boolean
  property_count: number
  properties: HierarchyProperty[]
}

export function SuperAdminHierarchyTab({
  onSelectProperty,
}: {
  onSelectProperty?: (propertyId: string) => void
}) {
  const qc = useQueryClient()
  const [expanded, setExpanded] = useState<Record<string, boolean>>({})

  const { data, isLoading } = useQuery({
    queryKey: ['admin-hierarchy'],
    queryFn: () => api.get('/admin/hierarchy').then((r) => r.data),
  })

  const customerAction = useMutation({
    mutationFn: ({ customerId, status }: { customerId: string; status: string }) =>
      api.patch(`/admin/customers/${customerId}/status`, { subscription_status: status }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin-hierarchy'] })
      toast.success('Business status updated')
    },
  })

  const approvalAction = useMutation({
    mutationFn: ({ approvalId, status }: { approvalId: string; status: string }) =>
      api.patch(`/admin/approvals/${approvalId}`, { status }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin-hierarchy'] })
      qc.invalidateQueries({ queryKey: ['admin-approvals'] })
      toast.success('Property approval updated')
    },
  })

  if (isLoading) return <p className="text-gray-400 text-sm">Loading hierarchy…</p>

  const customers: HierarchyCustomer[] = data?.customers || []

  return (
    <div className="space-y-4">
      <p className="text-sm text-gray-500">
        Navigate <strong>Business (customer)</strong> → <strong>Property</strong> → use sidebar links for rooms, tasks, modules, etc.
      </p>

      {customers.length === 0 ? (
        <p className="text-gray-400 text-sm">No businesses registered.</p>
      ) : (
        customers.map((c) => {
          const open = expanded[c.id] ?? true
          return (
            <div key={c.id} className="card">
              <div className="flex items-start justify-between gap-4">
                <button
                  type="button"
                  className="flex items-center gap-2 text-left flex-1"
                  onClick={() => setExpanded((e) => ({ ...e, [c.id]: !open }))}
                >
                  {open ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                  <div>
                    <p className="font-semibold text-gray-900">{c.company_name}</p>
                    <p className="text-xs text-gray-500">{c.email} · {c.property_count} properties</p>
                  </div>
                </button>
                <div className="flex items-center gap-2 flex-wrap justify-end">
                  <Badge variant={c.subscription_status === 'active' ? 'green' : 'yellow'}>{c.subscription_status}</Badge>
                  {c.subscription_status !== 'active' && (
                    <button
                      type="button"
                      className="btn-primary text-xs px-2 py-1"
                      onClick={() => customerAction.mutate({ customerId: c.id, status: 'active' })}
                    >
                      Approve business
                    </button>
                  )}
                  {c.subscription_status === 'active' && (
                    <button
                      type="button"
                      className="btn-secondary text-xs px-2 py-1 text-orange-600"
                      onClick={() => customerAction.mutate({ customerId: c.id, status: 'suspended' })}
                    >
                      Suspend
                    </button>
                  )}
                </div>
              </div>

              {open && (
                <div className="mt-4 pl-6 border-l-2 border-gray-100 space-y-2">
                  {c.properties.map((p) => (
                    <div key={p.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center gap-2">
                        <Building2 className="w-4 h-4 text-gray-400" />
                        <div>
                          <p className="text-sm font-medium text-gray-900">{p.name}</p>
                          <p className="text-xs text-gray-500">
                            {p.subscription_status}
                            {p.approval?.status && ` · approval: ${p.approval.status}`}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {p.approval?.id && p.approval.status === 'pending' && (
                          <>
                            <button
                              type="button"
                              className="btn-primary text-xs px-2 py-1"
                              onClick={() => approvalAction.mutate({ approvalId: p.approval!.id, status: 'approved' })}
                            >
                              Approve
                            </button>
                            <button
                              type="button"
                              className="btn-secondary text-xs px-2 py-1 text-red-600"
                              onClick={() => approvalAction.mutate({ approvalId: p.approval!.id, status: 'rejected' })}
                            >
                              Decline
                            </button>
                          </>
                        )}
                        <button
                          type="button"
                          className="btn-secondary text-xs px-2 py-1"
                          onClick={() => onSelectProperty?.(p.id)}
                        >
                          Modules
                        </button>
                        <Link
                          to={`/admin/rooms?property_id=${p.id}`}
                          className="text-xs text-blue-600 flex items-center gap-1 hover:underline"
                        >
                          Open <ExternalLink className="w-3 h-3" />
                        </Link>
                      </div>
                    </div>
                  ))}
                  {c.properties.length === 0 && (
                    <p className="text-xs text-gray-400">No properties linked to this business.</p>
                  )}
                </div>
              )}
            </div>
          )
        })
      )}

      {data?.unassigned_properties?.length > 0 && (
        <div className="card">
          <h4 className="font-medium text-gray-900 mb-2">Properties without business</h4>
          {data.unassigned_properties.map((p: HierarchyProperty & { id: string }) => (
            <div key={p.id} className="text-sm text-gray-600 py-1">{p.name} ({p.subscription_status})</div>
          ))}
        </div>
      )}
    </div>
  )
}
