import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, ClipboardList, Upload, CheckCircle, AlertTriangle } from 'lucide-react'
import api from '@/lib/api'
import type { Task } from '@/lib/types'
import { PriorityBadge, StatusBadge } from '@/components/ui/Badge'
import { Modal } from '@/components/ui/Modal'
import { PageLoader } from '@/components/ui/LoadingSpinner'
import toast from 'react-hot-toast'
import { useSelector } from 'react-redux'
import type { RootState } from '@/store'
import { formatDistanceToNow } from 'date-fns'

export function TasksPage() {
  const queryClient = useQueryClient()
  const user = useSelector((state: RootState) => state.auth.user)

  const [filterStatus, setFilterStatus] = useState('')
  const [filterPriority, setFilterPriority] = useState('')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [selectedTask, setSelectedTask] = useState<Task | null>(null)

  const [newTask, setNewTask] = useState({
    task_type: 'cleaning',
    service_type: '',
    priority: 'medium',
    description: '',
    property_id: user?.property_id || '',
    auto_assign: false,
  })

  const { data: tasks = [], isLoading } = useQuery<Task[]>({
    queryKey: ['tasks', user?.property_id, filterStatus, filterPriority],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (user?.property_id) params.set('property_id', user.property_id)
      if (user?.role === 'employee') params.set('assigned_to', user.id)
      if (filterStatus) params.set('status', filterStatus)
      if (filterPriority) params.set('priority', filterPriority)
      params.set('limit', '100')
      const { data } = await api.get(`/tasks?${params}`)
      return data
    },
  })

  const createTaskMutation = useMutation({
    mutationFn: (data: typeof newTask) =>
      api.post('/tasks', {
        ...data,
        service_type: data.service_type || undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
      setShowCreateModal(false)
      toast.success('Task created')
    },
  })

  const updateStatusMutation = useMutation({
    mutationFn: ({ taskId, status }: { taskId: string; status: string }) =>
      api.post(`/tasks/${taskId}/status`, { status }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      setSelectedTask(null)
      toast.success('Status updated')
    },
  })

  const autoAssignMutation = useMutation({
    mutationFn: (taskId: string) => api.post(`/tasks/${taskId}/auto-assign`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
      toast.success('Assigned to longest-idle free employee')
    },
  })

  const statusCounts = tasks.reduce((acc, t) => {
    acc[t.status] = (acc[t.status] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  if (isLoading) return <PageLoader />

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Tasks</h1>
          <p className="text-gray-500 text-sm">
          {tasks.length} total tasks · SLA policies:{' '}
          <code className="text-xs bg-gray-100 px-1 rounded">/api/v1/task-sla-policies</code>
        </p>
        </div>
        {user?.role !== 'employee' && (
          <button onClick={() => setShowCreateModal(true)} className="btn-primary flex items-center gap-2">
            <Plus className="w-4 h-4" />
            Create Task
          </button>
        )}
      </div>

      {/* Quick stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        {[
          { label: 'Pending', key: 'pending', color: 'gray' },
          { label: 'In Progress', key: 'in_progress', color: 'yellow' },
          { label: 'Verification', key: 'verification_pending', color: 'purple' },
          { label: 'Completed', key: 'completed', color: 'green' },
        ].map(({ label, key, color }) => (
          <div
            key={key}
            onClick={() => setFilterStatus(filterStatus === key ? '' : key)}
            className={`bg-white rounded-xl p-4 border-2 cursor-pointer transition-all ${filterStatus === key ? 'border-blue-500 shadow-md' : 'border-gray-100 hover:border-gray-200'}`}
          >
            <p className="text-2xl font-bold text-gray-900">{statusCounts[key] || 0}</p>
            <p className="text-sm text-gray-500">{label}</p>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex gap-3 mb-4">
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="border border-gray-200 rounded-lg px-3 py-2 text-sm bg-white"
        >
          <option value="">All Status</option>
          {['pending', 'assigned', 'in_progress', 'verification_pending', 'approved', 'completed', 'rejected'].map(s => (
            <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>
          ))}
        </select>
        <select
          value={filterPriority}
          onChange={(e) => setFilterPriority(e.target.value)}
          className="border border-gray-200 rounded-lg px-3 py-2 text-sm bg-white"
        >
          <option value="">All Priority</option>
          {['low', 'medium', 'high', 'critical'].map(p => <option key={p} value={p}>{p}</option>)}
        </select>
      </div>

      {/* Tasks list */}
      <div className="space-y-3">
        {tasks.map((task) => (
          <div
            key={task.id}
            onClick={() => setSelectedTask(task)}
            className="bg-white rounded-xl border border-gray-100 p-4 hover:shadow-sm cursor-pointer transition-all"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-semibold text-gray-900 capitalize">{task.task_type.replace(/_/g, ' ')}</span>
                  <PriorityBadge priority={task.priority} />
                  <StatusBadge status={task.status} />
                  {task.escalation_count > 0 && (
                    <span className="flex items-center gap-1 text-xs text-red-600 bg-red-50 px-2 py-0.5 rounded-full">
                      <AlertTriangle className="w-3 h-3" />
                      Escalated {task.escalation_count}x
                    </span>
                  )}
                  {task.sla_breached_at && (
                    <span className="text-xs text-red-700 bg-red-50 px-2 py-0.5 rounded-full border border-red-100">SLA breached</span>
                  )}
                </div>
                {task.description && (
                  <p className="text-sm text-gray-500 mt-1 truncate">{task.description}</p>
                )}
                <div className="flex items-center gap-4 mt-2 text-xs text-gray-400">
                  <span>Created {formatDistanceToNow(new Date(task.created_at), { addSuffix: true })}</span>
                  {task.due_time && (
                    <span className={new Date(task.due_time) < new Date() ? 'text-red-500' : ''}>
                      Due: {new Date(task.due_time).toLocaleString()}
                    </span>
                  )}
                  {task.sla_due_at && (
                    <span className={new Date(task.sla_due_at) < new Date() && !task.sla_breached_at ? 'text-amber-600' : 'text-gray-400'}>
                      SLA: {new Date(task.sla_due_at).toLocaleString()}
                    </span>
                  )}
                  {task.media.length > 0 && (
                    <span className="flex items-center gap-1">
                      <Upload className="w-3 h-3" />
                      {task.media.length} media
                    </span>
                  )}
                </div>
              </div>
              {task.status === 'pending' && user?.role !== 'employee' && (
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation()
                    autoAssignMutation.mutate(task.id)
                  }}
                  className="btn-primary text-xs px-3 py-1.5"
                  disabled={autoAssignMutation.isPending}
                >
                  Auto-assign
                </button>
              )}
              {task.status === 'verification_pending' && user?.role !== 'employee' && (
                <div className="flex gap-2">
                  <button
                    onClick={(e) => { e.stopPropagation(); updateStatusMutation.mutate({ taskId: task.id, status: 'approved' }) }}
                    className="text-xs px-3 py-1.5 bg-green-600 text-white rounded-lg hover:bg-green-700"
                  >
                    Approve
                  </button>
                  <button
                    onClick={(e) => { e.stopPropagation(); updateStatusMutation.mutate({ taskId: task.id, status: 'rejected' }) }}
                    className="text-xs px-3 py-1.5 bg-red-600 text-white rounded-lg hover:bg-red-700"
                  >
                    Reject
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}

        {tasks.length === 0 && (
          <div className="text-center py-12 text-gray-400">
            <ClipboardList className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>No tasks found</p>
          </div>
        )}
      </div>

      {/* Create Task Modal */}
      <Modal isOpen={showCreateModal} onClose={() => setShowCreateModal(false)} title="Create Task">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Task Type</label>
            <select className="input" value={newTask.task_type} onChange={(e) => setNewTask({ ...newTask, task_type: e.target.value })}>
              {['cleaning', 'maintenance', 'delivery', 'sanitization', 'inspection', 'laundry', 'other'].map(t => (
                <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Service type (for SLA)</label>
            <select
              className="input"
              value={newTask.service_type}
              onChange={(e) => setNewTask({ ...newTask, service_type: e.target.value })}
            >
              <option value="">Any</option>
              {['housekeeping', 'f_b', 'engineering', 'front_office'].map((s) => (
                <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>
              ))}
            </select>
          </div>
          <label className="flex items-center gap-2 text-sm text-gray-700">
            <input
              type="checkbox"
              checked={newTask.auto_assign}
              onChange={(e) => setNewTask({ ...newTask, auto_assign: e.target.checked })}
            />
            Auto-assign to longest-idle free employee
          </label>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
            <select className="input" value={newTask.priority} onChange={(e) => setNewTask({ ...newTask, priority: e.target.value })}>
              {['low', 'medium', 'high', 'critical'].map(p => <option key={p}>{p}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea
              className="input resize-none"
              rows={3}
              value={newTask.description}
              onChange={(e) => setNewTask({ ...newTask, description: e.target.value })}
              placeholder="Task details..."
            />
          </div>
          <div className="flex gap-3 pt-2">
            <button onClick={() => setShowCreateModal(false)} className="btn-secondary flex-1">Cancel</button>
            <button onClick={() => createTaskMutation.mutate(newTask)} disabled={createTaskMutation.isPending} className="btn-primary flex-1">
              {createTaskMutation.isPending ? 'Creating...' : 'Create Task'}
            </button>
          </div>
        </div>
      </Modal>

      {/* Task Detail Modal */}
      {selectedTask && (
        <Modal isOpen={!!selectedTask} onClose={() => setSelectedTask(null)} title="Task Details" size="lg">
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-xs text-gray-500 mb-1">Type</p>
                <p className="font-medium capitalize">{selectedTask.task_type.replace(/_/g, ' ')}</p>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-xs text-gray-500 mb-1">Priority</p>
                <PriorityBadge priority={selectedTask.priority} />
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-xs text-gray-500 mb-1">Status</p>
                <StatusBadge status={selectedTask.status} />
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-xs text-gray-500 mb-1">Created</p>
                <p className="text-sm">{new Date(selectedTask.created_at).toLocaleString()}</p>
              </div>
            </div>

            {selectedTask.description && (
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-xs text-gray-500 mb-1">Description</p>
                <p className="text-sm">{selectedTask.description}</p>
              </div>
            )}

            {(selectedTask.service_type || selectedTask.sla_due_at || selectedTask.sla_breached_at) && (
              <div className="p-3 bg-amber-50/80 border border-amber-100 rounded-lg text-sm space-y-1">
                <p className="text-xs font-semibold text-amber-900">SLA / RCA</p>
                {selectedTask.service_type && <p className="text-gray-700">Service type: {selectedTask.service_type}</p>}
                {selectedTask.sla_due_at && <p className="text-gray-700">SLA due: {new Date(selectedTask.sla_due_at).toLocaleString()}</p>}
                {selectedTask.root_cause_category && <p className="text-gray-700">Root-cause bucket: {selectedTask.root_cause_category}</p>}
                {selectedTask.sla_breached_at && (
                  <p className="text-red-700 font-medium">Breached at {new Date(selectedTask.sla_breached_at).toLocaleString()}</p>
                )}
              </div>
            )}

            {user?.role !== 'employee' && ['pending', 'assigned'].includes(selectedTask.status) && (
              <button
                type="button"
                className="btn-secondary w-full"
                disabled={autoAssignMutation.isPending}
                onClick={() => autoAssignMutation.mutate(selectedTask.id)}
              >
                Auto-assign (longest idle)
              </button>
            )}

            {selectedTask.media.length > 0 && (
              <div>
                <p className="text-sm font-medium text-gray-700 mb-2">Media ({selectedTask.media.length})</p>
                <div className="grid grid-cols-3 gap-2">
                  {selectedTask.media.map((m) => (
                    <div key={m.id} className="bg-gray-100 rounded-lg aspect-square flex items-center justify-center">
                      {m.media_type === 'photo' ? (
                        <img src={m.media_url} alt="task media" className="w-full h-full object-cover rounded-lg" />
                      ) : (
                        <video src={m.media_url} className="w-full h-full object-cover rounded-lg" />
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {user?.role !== 'employee' && selectedTask.status === 'verification_pending' && (
              <div className="flex gap-3">
                <button
                  onClick={() => updateStatusMutation.mutate({ taskId: selectedTask.id, status: 'approved' })}
                  className="btn-success flex-1 flex items-center justify-center gap-2"
                >
                  <CheckCircle className="w-4 h-4" />
                  Approve
                </button>
                <button
                  onClick={() => updateStatusMutation.mutate({ taskId: selectedTask.id, status: 'rejected' })}
                  className="btn-danger flex-1"
                >
                  Reject
                </button>
              </div>
            )}

            {user?.role === 'employee' && selectedTask.status === 'assigned' && (
              <button
                onClick={() => updateStatusMutation.mutate({ taskId: selectedTask.id, status: 'in_progress' })}
                className="btn-primary w-full"
              >
                Start Task
              </button>
            )}
          </div>
        </Modal>
      )}
    </div>
  )
}
