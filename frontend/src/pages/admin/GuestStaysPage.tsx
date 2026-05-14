import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { UserRound, LogIn, LogOut } from 'lucide-react'
import api from '@/lib/api'
import toast from 'react-hot-toast'
import { useSelector } from 'react-redux'
import type { RootState } from '@/store'
import type { Room } from '@/lib/types'
import { PageLoader } from '@/components/ui/LoadingSpinner'
import { Modal } from '@/components/ui/Modal'
import { useState } from 'react'

export function GuestStaysPage() {
  const qc = useQueryClient()
  const user = useSelector((s: RootState) => s.auth.user)
  const propertyId = user?.property_id
  const [showCheckIn, setShowCheckIn] = useState(false)
  const [roomId, setRoomId] = useState('')
  const [guestName, setGuestName] = useState('')
  const [guestPhone, setGuestPhone] = useState('')

  const { data: stays = [], isLoading } = useQuery({
    queryKey: ['guest-stays', propertyId],
    queryFn: () => api.get(`/rooms/guest-stays?property_id=${propertyId}`).then(r => r.data),
    enabled: !!propertyId,
  })

  const { data: vacantRooms = [] } = useQuery({
    queryKey: ['vacant-rooms', propertyId],
    queryFn: () =>
      api
        .get(`/rooms?property_id=${propertyId}&room_status=vacant&limit=200`)
        .then(r => r.data),
    enabled: !!propertyId && showCheckIn,
  })

  const checkInMut = useMutation({
    mutationFn: () =>
      api.post(`/rooms/${roomId}/guest-check-in`, {
        guest_name: guestName,
        guest_phone: guestPhone || undefined,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['guest-stays'] })
      qc.invalidateQueries({ queryKey: ['vacant-rooms'] })
      setShowCheckIn(false)
      setRoomId('')
      setGuestName('')
      setGuestPhone('')
      toast.success('Guest checked in')
    },
  })

  const checkoutMut = useMutation({
    mutationFn: (id: string) => api.post(`/rooms/${id}/checkout`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['guest-stays'] })
      toast.success('Checked out — cleaning task created')
    },
  })

  if (!propertyId) return <p className="text-gray-500">No property context.</p>
  if (isLoading) return <PageLoader />

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Guest stays</h1>
          <p className="text-gray-500 text-sm">Check-in / check-out and in-house guests</p>
        </div>
        <button
          className="btn-primary flex items-center gap-2"
          onClick={() => {
            setShowCheckIn(true)
            setRoomId('')
          }}
        >
          <LogIn className="w-4 h-4" /> Check-in
        </button>
      </div>

      <div className="space-y-3">
        {stays.map((r: Room) => (
          <div key={r.id} className="card flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-50 rounded-xl flex items-center justify-center">
                <UserRound className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <p className="font-semibold text-gray-900">Room {r.room_number}</p>
                <p className="text-sm text-gray-600">{r.guest_name}</p>
                {r.guest_phone && <p className="text-xs text-gray-400">{r.guest_phone}</p>}
                {r.check_in_time && (
                  <p className="text-xs text-gray-400 mt-1">In: {new Date(r.check_in_time).toLocaleString()}</p>
                )}
                {r.expected_check_out && (
                  <p className="text-xs text-amber-600">Expected out: {new Date(r.expected_check_out).toLocaleString()}</p>
                )}
              </div>
            </div>
            <button
              className="btn-secondary flex items-center gap-2 text-sm"
              onClick={() => checkoutMut.mutate(r.id)}
              disabled={checkoutMut.isPending}
            >
              <LogOut className="w-4 h-4" /> Check-out
            </button>
          </div>
        ))}
        {stays.length === 0 && <p className="text-gray-400 text-sm">No occupied rooms.</p>}
      </div>

      <Modal isOpen={showCheckIn} onClose={() => setShowCheckIn(false)} title="Guest check-in">
        <div className="space-y-3">
          <label className="text-sm text-gray-600">Room (vacant)</label>
          <select className="input" value={roomId} onChange={(e) => setRoomId(e.target.value)}>
            <option value="">Select room</option>
            {(vacantRooms as Room[]).map((room) => (
              <option key={room.id} value={room.id}>
                {room.room_number} — {room.room_category}
              </option>
            ))}
          </select>
          <input className="input" placeholder="Guest name *" value={guestName} onChange={(e) => setGuestName(e.target.value)} />
          <input className="input" placeholder="Phone" value={guestPhone} onChange={(e) => setGuestPhone(e.target.value)} />
          <button
            className="btn-primary w-full"
            disabled={!roomId || !guestName || checkInMut.isPending}
            onClick={() => checkInMut.mutate()}
          >
            Confirm check-in
          </button>
        </div>
      </Modal>
    </div>
  )
}
