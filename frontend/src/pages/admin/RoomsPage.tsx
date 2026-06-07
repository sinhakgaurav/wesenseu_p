import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, BedDouble, Search, Filter } from 'lucide-react'
import api from '@/lib/api'
import type { Room, PropertyRoomCategory } from '@/lib/types'
import { StatusBadge } from '@/components/ui/Badge'
import { Modal } from '@/components/ui/Modal'
import { PageLoader } from '@/components/ui/LoadingSpinner'
import toast from 'react-hot-toast'
import { useSelector } from 'react-redux'
import type { RootState } from '@/store'
import { usePropertyScope } from '@/context/PropertyScopeContext'
import { RequirePropertyScope } from '@/components/layout/RequirePropertyScope'

const ROOM_STATUS_OPTIONS = [
  { value: '', label: 'All Status' },
  { value: 'vacant', label: 'Vacant' },
  { value: 'occupied', label: 'Occupied' },
  { value: 'cleaning_pending', label: 'Cleaning Pending' },
  { value: 'cleaning_in_progress', label: 'Cleaning In Progress' },
  { value: 'ready', label: 'Ready' },
  { value: 'maintenance', label: 'Maintenance' },
  { value: 'inspection_pending', label: 'Inspection Pending' },
]

const STATUS_COLOR_MAP: Record<string, string> = {
  vacant: 'bg-green-50 border-green-200',
  occupied: 'bg-blue-50 border-blue-200',
  cleaning_pending: 'bg-yellow-50 border-yellow-200',
  cleaning_in_progress: 'bg-orange-50 border-orange-200',
  ready: 'bg-emerald-50 border-emerald-200',
  maintenance: 'bg-red-50 border-red-200',
  inspection_pending: 'bg-purple-50 border-purple-200',
  blocked: 'bg-gray-50 border-gray-200',
}

type NewRoomForm = {
  room_number: string
  room_category: string
  property_room_category_id: string
  floor_number: number
  property_id: string
}

export function RoomsPage() {
  const queryClient = useQueryClient()
  const user = useSelector((state: RootState) => state.auth.user)
  const { effectivePropertyId } = usePropertyScope()
  const propertyId = effectivePropertyId || ''
  const canManageRoom = user?.role === 'super_admin' || user?.role === 'property_manager'

  const [filterStatus, setFilterStatus] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedRoom, setSelectedRoom] = useState<Room | null>(null)
  const [showAddModal, setShowAddModal] = useState(false)
  const [showStatusModal, setShowStatusModal] = useState(false)
  const [newStatus, setNewStatus] = useState('')
  const [guestName, setGuestName] = useState('')
  const [editRoomNumber, setEditRoomNumber] = useState('')
  const [editFloor, setEditFloor] = useState(1)
  const [editCategoryId, setEditCategoryId] = useState('')

  const [newRoom, setNewRoom] = useState<NewRoomForm>({
    room_number: '',
    room_category: '',
    property_room_category_id: '',
    floor_number: 1,
    property_id: propertyId,
  })

  const { data: roomCategories = [] } = useQuery<PropertyRoomCategory[]>({
    queryKey: ['room-categories', propertyId],
    enabled: !!propertyId,
    queryFn: async () => {
      const { data } = await api.get(`/room-categories?property_id=${propertyId}`)
      return data
    },
  })

  const activeCategories = roomCategories.filter((c) => c.is_active)

  const { data: rooms = [], isLoading } = useQuery<Room[]>({
    queryKey: ['rooms', propertyId, filterStatus],
    enabled: !!propertyId,
    queryFn: async () => {
      const params = new URLSearchParams()
      if (propertyId) params.set('property_id', propertyId)
      if (filterStatus) params.set('room_status', filterStatus)
      params.set('limit', '200')
      const { data } = await api.get(`/rooms?${params}`)
      return data
    },
  })

  useEffect(() => {
    if (selectedRoom) {
      setGuestName(selectedRoom.guest_name || '')
      setEditRoomNumber(selectedRoom.room_number)
      setEditFloor(selectedRoom.floor_number ?? 1)
      setEditCategoryId(selectedRoom.property_room_category_id || '')
    }
  }, [selectedRoom])

  const addRoomMutation = useMutation({
    mutationFn: (data: NewRoomForm) => {
      const body: Record<string, unknown> = {
        room_number: data.room_number.trim(),
        floor_number: data.floor_number,
        property_id: data.property_id,
      }
      if (data.property_room_category_id) {
        body.property_room_category_id = data.property_room_category_id
      } else if (data.room_category.trim()) {
        body.room_category = data.room_category.trim()
      } else {
        return Promise.reject(new Error('Choose a room category from the catalog or enter a legacy label.'))
      }
      return api.post('/rooms', body)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rooms'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      setShowAddModal(false)
      toast.success('Room added successfully')
    },
    onError: (e: unknown) => {
      const msg = e && typeof e === 'object' && 'response' in e && (e as { response?: { data?: { detail?: string } } }).response?.data?.detail
      toast.error(typeof msg === 'string' ? msg : 'Could not add room')
    },
  })

  const patchRoomMutation = useMutation({
    mutationFn: () => {
      if (!selectedRoom) return Promise.reject()
      const body: Record<string, unknown> = {
        room_number: editRoomNumber.trim(),
        floor_number: editFloor,
      }
      if (editCategoryId) {
        body.property_room_category_id = editCategoryId
      } else {
        body.property_room_category_id = null
        body.room_category = selectedRoom.room_category
      }
      return api.patch(`/rooms/${selectedRoom.id}`, body)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rooms'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      toast.success('Room updated')
      setShowStatusModal(false)
    },
    onError: () => toast.error('Update failed'),
  })

  const deleteRoomMutation = useMutation({
    mutationFn: (roomId: string) => api.delete(`/rooms/${roomId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rooms'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      setShowStatusModal(false)
      setSelectedRoom(null)
      toast.success('Room removed')
    },
    onError: () => toast.error('Delete failed'),
  })

  const updateStatusMutation = useMutation({
    mutationFn: ({ roomId, status, guest_name }: { roomId: string; status: string; guest_name?: string }) =>
      api.post(`/rooms/${roomId}/status`, { room_status: status, guest_name }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rooms'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      setShowStatusModal(false)
      toast.success('Room status updated')
    },
  })

  const checkoutMutation = useMutation({
    mutationFn: (roomId: string) => api.post(`/rooms/${roomId}/checkout`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rooms'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      toast.success('Checkout completed. Cleaning task created.')
    },
  })

  const openAddModal = () => {
    const first = activeCategories[0]?.id ?? ''
    setNewRoom({
      room_number: '',
      room_category: '',
      property_room_category_id: first,
      floor_number: 1,
      property_id: propertyId,
    })
    setShowAddModal(true)
  }

  const filtered = rooms.filter(
    (r) =>
      r.room_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.room_category.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.guest_name?.toLowerCase().includes(searchQuery.toLowerCase())
  )

  if (isLoading) return <PageLoader />

  return (
    <RequirePropertyScope>
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Rooms</h1>
          <p className="text-gray-500 text-sm">{rooms.length} total rooms</p>
        </div>
        {canManageRoom && (
          <button type="button" onClick={openAddModal} className="btn-primary flex items-center gap-2">
            <Plus className="w-4 h-4" />
            Add Room
          </button>
        )}
      </div>

      <div className="flex flex-wrap gap-3 mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search rooms..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10 pr-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-gray-400" />
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="border border-gray-200 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {ROOM_STATUS_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3">
        {filtered.map((room) => (
          <div
            key={room.id}
            role="button"
            tabIndex={0}
            onClick={() => {
              setSelectedRoom(room)
              setShowStatusModal(true)
              setNewStatus(room.room_status)
            }}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                setSelectedRoom(room)
                setShowStatusModal(true)
                setNewStatus(room.room_status)
              }
            }}
            className={`border-2 rounded-xl p-4 cursor-pointer hover:shadow-md transition-all ${STATUS_COLOR_MAP[room.room_status] || 'bg-gray-50 border-gray-200'}`}
          >
            <div className="flex items-center justify-between mb-2">
              <BedDouble className="w-4 h-4 text-gray-500" />
              <span className="text-xs text-gray-400">{room.room_category?.[0] ?? '—'}</span>
            </div>
            <p className="text-lg font-bold text-gray-900">{room.room_number}</p>
            <p className="text-xs text-gray-500 mt-0.5">{room.room_category}</p>
            {room.floor_number != null && <p className="text-xs text-gray-400">Floor {room.floor_number}</p>}
            <div className="mt-2">
              <StatusBadge status={room.room_status} />
            </div>
            {room.guest_name && <p className="text-xs text-gray-600 mt-1 truncate">{room.guest_name}</p>}
          </div>
        ))}
      </div>

      <Modal isOpen={showAddModal} onClose={() => setShowAddModal(false)} title="Add New Room">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Room number</label>
            <input
              className="input"
              value={newRoom.room_number}
              onChange={(e) => setNewRoom({ ...newRoom, room_number: e.target.value })}
              placeholder="e.g., 101"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Category (from catalog)</label>
            <select
              className="input"
              value={newRoom.property_room_category_id}
              onChange={(e) =>
                setNewRoom({ ...newRoom, property_room_category_id: e.target.value, room_category: '' })
              }
            >
              <option value="">— use legacy label below —</option>
              {activeCategories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.display_name} ({c.code})
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-400 mt-1">Manage categories under Setup → Room Categories.</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Or legacy category label</label>
            <input
              className="input"
              value={newRoom.room_category}
              onChange={(e) => setNewRoom({ ...newRoom, room_category: e.target.value, property_room_category_id: '' })}
              placeholder="Only if no catalog row selected"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Floor number</label>
            <input
              type="number"
              className="input"
              value={newRoom.floor_number}
              onChange={(e) => setNewRoom({ ...newRoom, floor_number: Number(e.target.value) })}
            />
          </div>
          <div className="flex gap-3 pt-2">
            <button type="button" onClick={() => setShowAddModal(false)} className="btn-secondary flex-1">
              Cancel
            </button>
            <button
              type="button"
              onClick={() => addRoomMutation.mutate(newRoom)}
              disabled={addRoomMutation.isPending || !newRoom.room_number.trim()}
              className="btn-primary flex-1"
            >
              {addRoomMutation.isPending ? 'Adding…' : 'Add Room'}
            </button>
          </div>
        </div>
      </Modal>

      {selectedRoom && (
        <Modal
          isOpen={showStatusModal}
          onClose={() => setShowStatusModal(false)}
          title={`Room ${selectedRoom.room_number}`}
        >
          <div className="space-y-4">
            <div className="p-3 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600">
                <span className="font-medium">Category:</span> {selectedRoom.room_category}
              </p>
              <p className="text-sm text-gray-600">
                <span className="font-medium">Floor:</span> {selectedRoom.floor_number}
              </p>
              <p className="text-sm text-gray-600 flex items-center gap-2">
                <span className="font-medium">Current status:</span>
                <StatusBadge status={selectedRoom.room_status} />
              </p>
              {selectedRoom.guest_name && (
                <p className="text-sm text-gray-600">
                  <span className="font-medium">Guest:</span> {selectedRoom.guest_name}
                </p>
              )}
            </div>

            {canManageRoom && (
              <>
                <div className="border-t border-gray-200 pt-3">
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Room details (CRUD)</p>
                  <div className="space-y-2">
                    <div>
                      <label className="block text-xs text-gray-500 mb-1">Room number</label>
                      <input className="input" value={editRoomNumber} onChange={(e) => setEditRoomNumber(e.target.value)} />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-500 mb-1">Floor</label>
                      <input
                        type="number"
                        className="input"
                        value={editFloor}
                        onChange={(e) => setEditFloor(Number(e.target.value))}
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-500 mb-1">Catalog category</label>
                      <select
                        className="input"
                        value={editCategoryId}
                        onChange={(e) => setEditCategoryId(e.target.value)}
                      >
                        <option value="">Keep current label only</option>
                        {activeCategories.map((c) => (
                          <option key={c.id} value={c.id}>
                            {c.display_name}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="flex gap-2">
                      <button
                        type="button"
                        className="btn-secondary flex-1"
                        disabled={patchRoomMutation.isPending}
                        onClick={() => patchRoomMutation.mutate()}
                      >
                        Save details
                      </button>
                      <button
                        type="button"
                        className="btn-danger flex-1"
                        disabled={deleteRoomMutation.isPending}
                        onClick={() => {
                          if (confirm(`Remove room ${selectedRoom.room_number}?`)) deleteRoomMutation.mutate(selectedRoom.id)
                        }}
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                </div>
              </>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Update status</label>
              <select className="input" value={newStatus} onChange={(e) => setNewStatus(e.target.value)}>
                {ROOM_STATUS_OPTIONS.slice(1).map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </div>

            {newStatus === 'occupied' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Guest name</label>
                <input
                  className="input"
                  value={guestName}
                  onChange={(e) => setGuestName(e.target.value)}
                  placeholder="Enter guest name"
                />
              </div>
            )}

            <div className="flex flex-wrap gap-3">
              {selectedRoom.occupancy_status === 'occupied' && (
                <button
                  type="button"
                  onClick={() => {
                    checkoutMutation.mutate(selectedRoom.id)
                    setShowStatusModal(false)
                  }}
                  className="btn-danger flex-1 min-w-[120px]"
                >
                  Checkout guest
                </button>
              )}
              <button type="button" onClick={() => setShowStatusModal(false)} className="btn-secondary flex-1 min-w-[100px]">
                Close
              </button>
              <button
                type="button"
                onClick={() =>
                  updateStatusMutation.mutate({
                    roomId: selectedRoom.id,
                    status: newStatus,
                    guest_name: guestName || undefined,
                  })
                }
                disabled={updateStatusMutation.isPending}
                className="btn-primary flex-1 min-w-[100px]"
              >
                Update status
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
    </RequirePropertyScope>
  )
}
