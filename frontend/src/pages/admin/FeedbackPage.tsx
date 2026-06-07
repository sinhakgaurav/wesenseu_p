import { useQuery } from '@tanstack/react-query'
import { Star, TrendingUp, ThumbsUp, ThumbsDown, Minus } from 'lucide-react'
import api from '@/lib/api'
import { PageLoader } from '@/components/ui/LoadingSpinner'
import { formatDistanceToNow } from 'date-fns'
import { useAdminPropertyId } from '@/hooks/useAdminPropertyId'
import { RequirePropertyScope } from '@/components/layout/RequirePropertyScope'

interface Feedback {
  id: string
  room_id?: string
  guest_name?: string
  rating: number
  review_text?: string
  sentiment_label?: string
  sentiment_score?: number
  created_at: string
  source: string
}

interface FeedbackSummary {
  avg_rating: number
  total_feedback: number
  positive: number
  negative: number
  neutral: number
}

export function FeedbackPage() {
  const { propertyId, enabled } = useAdminPropertyId()

  const { data: feedbacks = [], isLoading } = useQuery<Feedback[]>({
    queryKey: ['feedback', propertyId],
    enabled,
    queryFn: async () => {
      const { data } = await api.get(`/feedback?property_id=${propertyId}&limit=50`)
      return data
    },
  })

  const { data: summary } = useQuery<FeedbackSummary>({
    queryKey: ['feedback-summary', propertyId],
    enabled,
    queryFn: async () => {
      const { data } = await api.get(`/feedback/summary?property_id=${propertyId}`)
      return data
    },
  })

  if (isLoading) return <PageLoader />

  const sentimentIcon = (label?: string) => {
    if (label === 'positive') return <ThumbsUp className="w-4 h-4 text-green-500" />
    if (label === 'negative') return <ThumbsDown className="w-4 h-4 text-red-500" />
    return <Minus className="w-4 h-4 text-gray-400" />
  }

  return (
    <RequirePropertyScope>
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Guest Feedback</h1>
          <p className="text-gray-500 text-sm">{summary?.total_feedback || 0} total reviews</p>
        </div>
      </div>

      {/* Summary cards */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="card text-center">
            <div className="flex items-center justify-center gap-1 mb-1">
              {[1, 2, 3, 4, 5].map((s) => (
                <Star key={s} className={`w-4 h-4 ${s <= Math.round(summary.avg_rating) ? 'fill-yellow-400 text-yellow-400' : 'text-gray-200'}`} />
              ))}
            </div>
            <p className="text-3xl font-bold text-gray-900">{summary.avg_rating}</p>
            <p className="text-sm text-gray-500">Average Rating</p>
          </div>
          <div className="card text-center">
            <ThumbsUp className="w-8 h-8 text-green-500 mx-auto mb-1" />
            <p className="text-3xl font-bold text-gray-900">{summary.positive}</p>
            <p className="text-sm text-gray-500">Positive</p>
          </div>
          <div className="card text-center">
            <ThumbsDown className="w-8 h-8 text-red-500 mx-auto mb-1" />
            <p className="text-3xl font-bold text-gray-900">{summary.negative}</p>
            <p className="text-sm text-gray-500">Negative</p>
          </div>
          <div className="card text-center">
            <TrendingUp className="w-8 h-8 text-blue-500 mx-auto mb-1" />
            <p className="text-3xl font-bold text-gray-900">{summary.total_feedback}</p>
            <p className="text-sm text-gray-500">Total Reviews</p>
          </div>
        </div>
      )}

      {/* Feedback list */}
      <div className="space-y-3">
        {feedbacks.map((fb) => (
          <div key={fb.id} className="card">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <div className="flex items-center gap-0.5">
                    {[1, 2, 3, 4, 5].map((s) => (
                      <Star key={s} className={`w-4 h-4 ${s <= fb.rating ? 'fill-yellow-400 text-yellow-400' : 'text-gray-200'}`} />
                    ))}
                  </div>
                  {sentimentIcon(fb.sentiment_label)}
                  {fb.guest_name && <span className="text-sm font-medium text-gray-700">{fb.guest_name}</span>}
                  <span className="text-xs text-gray-400 ml-auto">
                    {formatDistanceToNow(new Date(fb.created_at), { addSuffix: true })}
                  </span>
                </div>
                {fb.review_text && <p className="text-sm text-gray-600">{fb.review_text}</p>}
              </div>
            </div>
          </div>
        ))}

        {feedbacks.length === 0 && (
          <div className="text-center py-12 text-gray-400">
            <Star className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>No feedback yet</p>
          </div>
        )}
      </div>
    </div>
    </RequirePropertyScope>
  )
}
