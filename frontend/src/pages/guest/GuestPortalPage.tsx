import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { MessageSquare, Star, ShoppingCart, Shield, CheckCircle, Send } from 'lucide-react'
import api from '@/lib/api'
import type { Room } from '@/lib/types'
import toast from 'react-hot-toast'

const COMPLAINT_TYPES = [
  { value: 'complaint', label: '🚨 Report a Problem' },
  { value: 'service_request', label: '🛎️ Service Request' },
  { value: 'housekeeping', label: '🧹 Housekeeping' },
  { value: 'maintenance', label: '🔧 Maintenance' },
  { value: 'feedback', label: '💬 General Feedback' },
]

const SERVICE_ITEMS = [
  'Extra Towels', 'Extra Toiletries', 'Extra Pillows', 'Water Bottles',
  'Room Cleaning', 'Extra Bed', 'Baby Crib', 'Wheelchair', 'Food Order',
  'Laundry Service', 'Wake Up Call', 'Taxi Booking',
]

export function GuestPortalPage() {
  const { roomId } = useParams<{ roomId: string }>()
  const [activeTab, setActiveTab] = useState<'request' | 'feedback'>('request')
  const [submitted, setSubmitted] = useState(false)

  const [ticketForm, setTicketForm] = useState({
    title: '',
    ticket_type: 'complaint',
    priority: 'medium',
    description: '',
    guest_name: '',
    guest_phone: '',
  })

  const [feedbackForm, setFeedbackForm] = useState({
    rating: 0,
    review_text: '',
    guest_name: '',
    guest_phone: '',
    department_id: '',
  })

  const [selectedServices, setSelectedServices] = useState<string[]>([])

  const { data: room } = useQuery<Room>({
    queryKey: ['room-qr', roomId],
    queryFn: async () => {
      const { data } = await api.get(`/rooms/${roomId}/by-qr`)
      return data
    },
    enabled: !!roomId,
  })

  const ticketMutation = useMutation({
    mutationFn: (data: typeof ticketForm & { property_id: string; room_id: string }) =>
      api.post('/tickets/guest', data),
    onSuccess: () => {
      setSubmitted(true)
      toast.success('Your request has been submitted!')
    },
    onError: () => {
      toast.error('Failed to submit. Please try again.')
    },
  })

  const feedbackMutation = useMutation({
    mutationFn: (data: typeof feedbackForm & { property_id: string; room_id: string }) =>
      api.post('/feedback', data),
    onSuccess: () => {
      setSubmitted(true)
      toast.success('Thank you for your feedback!')
    },
  })

  const handleTicketSubmit = () => {
    if (!ticketForm.title || !room) return
    const description = selectedServices.length > 0
      ? `Services requested: ${selectedServices.join(', ')}. ${ticketForm.description}`
      : ticketForm.description

    ticketMutation.mutate({
      ...ticketForm,
      description,
      property_id: room.property_id,
      room_id: roomId!,
    })
  }

  const handleFeedbackSubmit = () => {
    if (!feedbackForm.rating || !room) return
    feedbackMutation.mutate({
      ...feedbackForm,
      property_id: room.property_id,
      room_id: roomId!,
    })
  }

  if (submitted) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-900 to-indigo-900 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl p-8 max-w-sm w-full text-center shadow-2xl">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle className="w-8 h-8 text-green-600" />
          </div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">Submitted Successfully</h2>
          <p className="text-gray-500 text-sm mb-6">
            Our team has been notified and will respond shortly. Your ticket number will be sent to you.
          </p>
          <button
            onClick={() => { setSubmitted(false); setTicketForm({ title: '', ticket_type: 'complaint', priority: 'medium', description: '', guest_name: '', guest_phone: '' }); setFeedbackForm({ rating: 0, review_text: '', guest_name: '', guest_phone: '', department_id: '' }); setSelectedServices([]) }}
            className="btn-primary w-full"
          >
            Submit Another Request
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 to-indigo-900">
      {/* Header */}
      <div className="text-center pt-10 pb-6 px-4">
        <div className="w-14 h-14 bg-white/20 rounded-2xl flex items-center justify-center mx-auto mb-3 backdrop-blur-sm">
          <Shield className="w-7 h-7 text-white" />
        </div>
        <h1 className="text-2xl font-bold text-white">Monitour</h1>
        {room && (
          <p className="text-blue-200 text-sm mt-1">Room {room.room_number} • {room.room_category}</p>
        )}
      </div>

      {/* Card */}
      <div className="max-w-md mx-auto px-4 pb-8">
        <div className="bg-white rounded-2xl shadow-2xl overflow-hidden">
          {/* Tabs */}
          <div className="flex border-b border-gray-100">
            <button
              onClick={() => setActiveTab('request')}
              className={`flex-1 py-4 text-sm font-semibold flex items-center justify-center gap-2 transition-colors ${activeTab === 'request' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
            >
              <MessageSquare className="w-4 h-4" />
              Request / Complaint
            </button>
            <button
              onClick={() => setActiveTab('feedback')}
              className={`flex-1 py-4 text-sm font-semibold flex items-center justify-center gap-2 transition-colors ${activeTab === 'feedback' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
            >
              <Star className="w-4 h-4" />
              Feedback
            </button>
          </div>

          <div className="p-6">
            {activeTab === 'request' ? (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Request Type</label>
                  <div className="space-y-2">
                    {COMPLAINT_TYPES.map((type) => (
                      <label
                        key={type.value}
                        className={`flex items-center gap-3 p-3 rounded-xl border-2 cursor-pointer transition-all ${ticketForm.ticket_type === type.value ? 'border-blue-500 bg-blue-50' : 'border-gray-100 hover:border-gray-200'}`}
                      >
                        <input
                          type="radio"
                          name="ticket_type"
                          value={type.value}
                          checked={ticketForm.ticket_type === type.value}
                          onChange={(e) => setTicketForm({ ...ticketForm, ticket_type: e.target.value })}
                          className="accent-blue-600"
                        />
                        <span className="text-sm font-medium">{type.label}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {ticketForm.ticket_type === 'service_request' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      <ShoppingCart className="inline w-4 h-4 mr-1" />
                      Select Services
                    </label>
                    <div className="grid grid-cols-2 gap-2">
                      {SERVICE_ITEMS.map((service) => (
                        <label
                          key={service}
                          className={`flex items-center gap-2 p-2.5 rounded-lg border cursor-pointer text-sm transition-all ${selectedServices.includes(service) ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-gray-200 hover:border-gray-300'}`}
                        >
                          <input
                            type="checkbox"
                            checked={selectedServices.includes(service)}
                            onChange={(e) => {
                              if (e.target.checked) setSelectedServices([...selectedServices, service])
                              else setSelectedServices(selectedServices.filter(s => s !== service))
                            }}
                            className="accent-blue-600"
                          />
                          {service}
                        </label>
                      ))}
                    </div>
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Summary *</label>
                  <input
                    className="input"
                    value={ticketForm.title}
                    onChange={(e) => setTicketForm({ ...ticketForm, title: e.target.value })}
                    placeholder="Brief description of your issue"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Details (optional)</label>
                  <textarea
                    className="input resize-none"
                    rows={3}
                    value={ticketForm.description}
                    onChange={(e) => setTicketForm({ ...ticketForm, description: e.target.value })}
                    placeholder="Any additional details..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Your Name (optional)</label>
                  <input className="input" value={ticketForm.guest_name} onChange={(e) => setTicketForm({ ...ticketForm, guest_name: e.target.value })} placeholder="Your name" />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Phone (optional)</label>
                  <input type="tel" className="input" value={ticketForm.guest_phone} onChange={(e) => setTicketForm({ ...ticketForm, guest_phone: e.target.value })} placeholder="+91 XXXXX XXXXX" />
                </div>

                <button
                  onClick={handleTicketSubmit}
                  disabled={!ticketForm.title || ticketMutation.isPending}
                  className="btn-primary w-full flex items-center justify-center gap-2 py-3"
                >
                  <Send className="w-4 h-4" />
                  {ticketMutation.isPending ? 'Submitting...' : 'Submit Request'}
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3 text-center">How was your experience?</label>
                  <div className="flex justify-center gap-3">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <button
                        key={star}
                        onClick={() => setFeedbackForm({ ...feedbackForm, rating: star })}
                        className="transition-transform hover:scale-110 active:scale-95"
                      >
                        <Star
                          className={`w-10 h-10 ${feedbackForm.rating >= star ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300'}`}
                        />
                      </button>
                    ))}
                  </div>
                  {feedbackForm.rating > 0 && (
                    <p className="text-center text-sm text-gray-500 mt-2">
                      {['', 'Poor', 'Fair', 'Good', 'Very Good', 'Excellent'][feedbackForm.rating]}
                    </p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Write a Review (optional)</label>
                  <textarea
                    className="input resize-none"
                    rows={4}
                    value={feedbackForm.review_text}
                    onChange={(e) => setFeedbackForm({ ...feedbackForm, review_text: e.target.value })}
                    placeholder="Share your experience with us..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Your Name (optional)</label>
                  <input className="input" value={feedbackForm.guest_name} onChange={(e) => setFeedbackForm({ ...feedbackForm, guest_name: e.target.value })} placeholder="Your name" />
                </div>

                <button
                  onClick={handleFeedbackSubmit}
                  disabled={!feedbackForm.rating || feedbackMutation.isPending}
                  className="btn-primary w-full flex items-center justify-center gap-2 py-3"
                >
                  <Send className="w-4 h-4" />
                  {feedbackMutation.isPending ? 'Submitting...' : 'Submit Feedback'}
                </button>
              </div>
            )}
          </div>
        </div>

        <p className="text-center text-white/40 text-xs mt-4">Powered by Monitour</p>
      </div>
    </div>
  )
}
