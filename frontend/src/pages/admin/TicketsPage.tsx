import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Ticket, MessageSquare, Clock } from 'lucide-react'
import api from '@/lib/api'
import type { Ticket as TicketType } from '@/lib/types'
import { PriorityBadge, StatusBadge } from '@/components/ui/Badge'
import { Modal } from '@/components/ui/Modal'
import { PageLoader } from '@/components/ui/LoadingSpinner'
import toast from 'react-hot-toast'
import { useSelector } from 'react-redux'
import type { RootState } from '@/store'
import { formatDistanceToNow } from 'date-fns'

const TICKET_TYPES = ['complaint', 'service_request', 'maintenance', 'housekeeping', 'feedback', 'emergency']

export function TicketsPage() {
  const queryClient = useQueryClient()
  const user = useSelector((state: RootState) => state.auth.user)

  const [filterStatus, setFilterStatus] = useState('')
  const [filterPriority, setFilterPriority] = useState('')
  const [filterType, setFilterType] = useState('')
  const [selectedTicket, setSelectedTicket] = useState<TicketType | null>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newComment, setNewComment] = useState('')

  const [newTicket, setNewTicket] = useState({
    title: '',
    ticket_type: 'complaint',
    priority: 'medium',
    description: '',
    property_id: user?.property_id || '',
    created_by_guest: false,
  })

  const { data: tickets = [], isLoading } = useQuery<TicketType[]>({
    queryKey: ['tickets', user?.property_id, filterStatus, filterPriority, filterType],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (user?.property_id) params.set('property_id', user.property_id)
      if (filterStatus) params.set('status', filterStatus)
      if (filterPriority) params.set('priority', filterPriority)
      if (filterType) params.set('ticket_type', filterType)
      params.set('limit', '100')
      const { data } = await api.get(`/tickets?${params}`)
      return data
    },
  })

  const createTicketMutation = useMutation({
    mutationFn: (data: typeof newTicket) => api.post('/tickets', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tickets'] })
      setShowCreateModal(false)
      toast.success('Ticket created')
    },
  })

  const updateTicketMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Record<string, unknown> }) => api.patch(`/tickets/${id}`, data),
    onSuccess: (_, vars) => {
      queryClient.invalidateQueries({ queryKey: ['tickets'] })
      if (selectedTicket?.id === vars.id) {
        setSelectedTicket(null)
      }
      toast.success('Ticket updated')
    },
  })

  const addCommentMutation = useMutation({
    mutationFn: ({ ticketId, comment }: { ticketId: string; comment: string }) =>
      api.post(`/tickets/${ticketId}/comments`, { comment }),
    onSuccess: (_, vars) => {
      queryClient.invalidateQueries({ queryKey: ['tickets'] })
      queryClient.invalidateQueries({ queryKey: ['ticket', vars.ticketId] })
      setNewComment('')
      toast.success('Comment added')
    },
  })

  const priorityOrder = { critical: 0, high: 1, medium: 2, low: 3 }
  const sorted = [...tickets].sort((a, b) =>
    (priorityOrder[a.priority as keyof typeof priorityOrder] ?? 3) -
    (priorityOrder[b.priority as keyof typeof priorityOrder] ?? 3)
  )

  const statusCounts = tickets.reduce((acc, t) => {
    const key = ['open', 'assigned', 'in_progress'].includes(t.status) ? 'active' : t.status
    acc[key] = (acc[key] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  if (isLoading) return <PageLoader />

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Tickets</h1>
          <p className="text-gray-500 text-sm">{tickets.length} total tickets</p>
        </div>
        <button onClick={() => setShowCreateModal(true)} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" />
          New Ticket
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        {[
          { label: 'Active', key: 'active', color: 'blue' },
          { label: 'Resolved Today', key: 'resolved', color: 'green' },
          { label: 'Escalated', key: 'escalated', color: 'red' },
          { label: 'Closed', key: 'closed', color: 'gray' },
        ].map(({ label, key }) => (
          <div key={key} className="bg-white rounded-xl p-4 border border-gray-100">
            <p className="text-2xl font-bold text-gray-900">{statusCounts[key] || 0}</p>
            <p className="text-sm text-gray-500">{label}</p>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-4">
        <select className="border border-gray-200 rounded-lg px-3 py-2 text-sm bg-white" value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
          <option value="">All Status</option>
          {['open', 'assigned', 'in_progress', 'resolved', 'closed', 'escalated'].map(s => <option key={s} value={s}>{s}</option>)}
        </select>
        <select className="border border-gray-200 rounded-lg px-3 py-2 text-sm bg-white" value={filterPriority} onChange={(e) => setFilterPriority(e.target.value)}>
          <option value="">All Priority</option>
          {['low', 'medium', 'high', 'critical'].map(p => <option key={p} value={p}>{p}</option>)}
        </select>
        <select className="border border-gray-200 rounded-lg px-3 py-2 text-sm bg-white" value={filterType} onChange={(e) => setFilterType(e.target.value)}>
          <option value="">All Types</option>
          {TICKET_TYPES.map(t => <option key={t} value={t}>{t.replace(/_/g, ' ')}</option>)}
        </select>
      </div>

      {/* Tickets */}
      <div className="space-y-3">
        {sorted.map((ticket) => (
          <div
            key={ticket.id}
            onClick={() => setSelectedTicket(ticket)}
            className="bg-white rounded-xl border border-gray-100 p-4 hover:shadow-sm cursor-pointer transition-all"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap mb-1">
                  <span className="text-xs font-mono text-gray-400">{ticket.ticket_number}</span>
                  <PriorityBadge priority={ticket.priority} />
                  <StatusBadge status={ticket.status} />
                  <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full capitalize">
                    {ticket.ticket_type.replace(/_/g, ' ')}
                  </span>
                </div>
                <p className="font-medium text-gray-900">{ticket.title}</p>
                {ticket.description && (
                  <p className="text-sm text-gray-500 mt-0.5 truncate">{ticket.description}</p>
                )}
                <div className="flex items-center gap-4 mt-2 text-xs text-gray-400">
                  {ticket.guest_name && <span>By: {ticket.guest_name}</span>}
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {formatDistanceToNow(new Date(ticket.created_at), { addSuffix: true })}
                  </span>
                  {ticket.comments.length > 0 && (
                    <span className="flex items-center gap-1">
                      <MessageSquare className="w-3 h-3" />
                      {ticket.comments.length}
                    </span>
                  )}
                  {ticket.sla_deadline && new Date(ticket.sla_deadline) < new Date() && ticket.status !== 'resolved' && (
                    <span className="text-red-500 font-medium">SLA Breached</span>
                  )}
                </div>
              </div>
              {ticket.status === 'open' && (
                <button
                  onClick={(e) => { e.stopPropagation(); updateTicketMutation.mutate({ id: ticket.id, data: { status: 'in_progress' } }) }}
                  className="btn-primary text-xs px-3 py-1.5 flex-shrink-0"
                >
                  Start
                </button>
              )}
            </div>
          </div>
        ))}

        {tickets.length === 0 && (
          <div className="text-center py-12 text-gray-400">
            <Ticket className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>No tickets found</p>
          </div>
        )}
      </div>

      {/* Create Ticket Modal */}
      <Modal isOpen={showCreateModal} onClose={() => setShowCreateModal(false)} title="Create Ticket">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
            <input className="input" value={newTicket.title} onChange={(e) => setNewTicket({ ...newTicket, title: e.target.value })} placeholder="Brief description of the issue" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
              <select className="input" value={newTicket.ticket_type} onChange={(e) => setNewTicket({ ...newTicket, ticket_type: e.target.value })}>
                {TICKET_TYPES.map(t => <option key={t} value={t}>{t.replace(/_/g, ' ')}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
              <select className="input" value={newTicket.priority} onChange={(e) => setNewTicket({ ...newTicket, priority: e.target.value })}>
                {['low', 'medium', 'high', 'critical'].map(p => <option key={p}>{p}</option>)}
              </select>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea className="input resize-none" rows={3} value={newTicket.description} onChange={(e) => setNewTicket({ ...newTicket, description: e.target.value })} placeholder="Detailed description..." />
          </div>
          <div className="flex gap-3 pt-2">
            <button onClick={() => setShowCreateModal(false)} className="btn-secondary flex-1">Cancel</button>
            <button onClick={() => createTicketMutation.mutate(newTicket)} disabled={createTicketMutation.isPending || !newTicket.title} className="btn-primary flex-1">
              {createTicketMutation.isPending ? 'Creating...' : 'Create Ticket'}
            </button>
          </div>
        </div>
      </Modal>

      {/* Ticket Detail Modal */}
      {selectedTicket && (
        <Modal isOpen={!!selectedTicket} onClose={() => setSelectedTicket(null)} title={`Ticket ${selectedTicket.ticket_number}`} size="lg">
          <div className="space-y-4">
            <div className="flex items-center gap-2 flex-wrap">
              <PriorityBadge priority={selectedTicket.priority} />
              <StatusBadge status={selectedTicket.status} />
              <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full capitalize">
                {selectedTicket.ticket_type.replace(/_/g, ' ')}
              </span>
            </div>

            <div>
              <h3 className="font-semibold text-gray-900">{selectedTicket.title}</h3>
              {selectedTicket.description && <p className="text-sm text-gray-600 mt-1">{selectedTicket.description}</p>}
            </div>

            {selectedTicket.guest_name && (
              <p className="text-sm text-gray-500">Reported by: <span className="font-medium">{selectedTicket.guest_name}</span></p>
            )}

            {/* Status actions */}
            {!['resolved', 'closed'].includes(selectedTicket.status) && (
              <div className="flex gap-2 flex-wrap">
                {selectedTicket.status === 'open' && (
                  <button onClick={() => updateTicketMutation.mutate({ id: selectedTicket.id, data: { status: 'in_progress' } })} className="btn-primary text-sm px-3 py-1.5">Start Working</button>
                )}
                {selectedTicket.status === 'in_progress' && (
                  <button onClick={() => updateTicketMutation.mutate({ id: selectedTicket.id, data: { status: 'resolved' } })} className="btn-success text-sm px-3 py-1.5">Mark Resolved</button>
                )}
                <button onClick={() => updateTicketMutation.mutate({ id: selectedTicket.id, data: { status: 'escalated' } })} className="btn-danger text-sm px-3 py-1.5">Escalate</button>
              </div>
            )}

            {/* Comments */}
            <div>
              <h4 className="text-sm font-semibold text-gray-700 mb-2">Comments ({selectedTicket.comments.length})</h4>
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {selectedTicket.comments.map((c) => (
                  <div key={c.id} className="p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-medium text-gray-700">{c.author_name || 'Guest'}</span>
                      <span className="text-xs text-gray-400">{formatDistanceToNow(new Date(c.created_at), { addSuffix: true })}</span>
                    </div>
                    <p className="text-sm text-gray-600">{c.comment}</p>
                  </div>
                ))}
              </div>
              <div className="flex gap-2 mt-3">
                <input className="input flex-1" value={newComment} onChange={(e) => setNewComment(e.target.value)} placeholder="Add a comment..." />
                <button
                  onClick={() => addCommentMutation.mutate({ ticketId: selectedTicket.id, comment: newComment })}
                  disabled={!newComment || addCommentMutation.isPending}
                  className="btn-primary px-4"
                >
                  Send
                </button>
              </div>
            </div>
          </div>
        </Modal>
      )}
    </div>
  )
}
