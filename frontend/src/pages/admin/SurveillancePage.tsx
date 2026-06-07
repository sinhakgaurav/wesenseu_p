import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Camera, AlertTriangle, Shield, Eye, Plus, Wifi, Trash2, Power, RefreshCw } from 'lucide-react'
import { Badge } from '@/components/ui/Badge'
import api from '@/lib/api'
import toast from 'react-hot-toast'
import { useAdminPropertyId } from '@/hooks/useAdminPropertyId'
import { RequirePropertyScope } from '@/components/layout/RequirePropertyScope'

const severityColors: Record<string, string> = {
  critical: 'red', high: 'orange', medium: 'yellow', low: 'green',
}

export function SurveillancePage() {
  const { propertyId, enabled } = useAdminPropertyId()
  const qc = useQueryClient()
  const [showDiscover, setShowDiscover] = useState(false)
  const [discoveredCams, setDiscoveredCams] = useState<any[]>([])

  const { data: cameras = [], isLoading: camsLoading } = useQuery({
    queryKey: ['cameras', propertyId],
    queryFn: () => api.get(`/surveillance/cameras${propertyId ? `?property_id=${propertyId}` : ''}`).then(r => r.data),
  })

  const { data: scenarioPack } = useQuery({
    queryKey: ['surveillance-hotel-scenarios'],
    queryFn: () => api.get('/surveillance/hotel-surveillance-scenarios').then(r => r.data),
  })
  const scenarios = scenarioPack?.scenarios ?? []

  const { data: events = [], isLoading: eventsLoading, refetch: refetchEvents } = useQuery({
    queryKey: ['surveillance-events', propertyId],
    enabled,
    queryFn: () => api.get(`/surveillance/events?property_id=${propertyId}`).then(r => r.data),
    refetchInterval: 30000,
  })

  const ackEvent = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      api.patch(`/surveillance/events/${id}/status`, { status }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['surveillance-events'] })
      toast.success('Event updated')
    },
  })

  const toggleAI = useMutation({
    mutationFn: (cameraId: string) => api.post(`/surveillance/cameras/${cameraId}/toggle-ai`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['cameras'] }); toast.success('AI monitoring toggled') },
  })

  const addCamera = useMutation({
    mutationFn: (cam: any) => api.post('/surveillance/cameras', {
      property_id: propertyId,
      name: cam.model,
      location: cam.ip,
      stream_url: cam.rtsp_url,
      camera_type: 'ip',
    }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['cameras'] }); toast.success('Camera added') },
  })

  const deleteCamera = useMutation({
    mutationFn: (id: string) => api.delete(`/surveillance/cameras/${id}`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['cameras'] }); toast.success('Camera removed') },
  })

  const handleDiscover = async () => {
    try {
      const { data } = await api.post(`/surveillance/cameras/discover?property_id=${propertyId}`)
      setDiscoveredCams(data.discovered || [])
      setShowDiscover(true)
    } catch {
      toast.error('Discovery failed')
    }
  }

  const openCount = events.filter((e: any) => e.status === 'open').length

  return (
    <RequirePropertyScope>
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Surveillance & CCTV</h1>
          <p className="text-gray-500 text-sm">AI-Powered CCTV Monitoring</p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={handleDiscover} className="btn-secondary flex items-center gap-2 text-sm">
            <Wifi className="w-4 h-4" /> Discover Cameras
          </button>
          <div className="flex items-center gap-2 bg-green-50 border border-green-200 rounded-lg px-3 py-2">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            <span className="text-sm text-green-700 font-medium">Live Monitoring</span>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="card flex items-center gap-3">
          <div className="w-10 h-10 bg-blue-50 rounded-xl flex items-center justify-center">
            <Camera className="w-5 h-5 text-blue-600" />
          </div>
          <div>
            <p className="text-xl font-bold text-gray-900">{cameras.length}</p>
            <p className="text-xs text-gray-500">Total Cameras</p>
          </div>
        </div>
        <div className="card flex items-center gap-3">
          <div className="w-10 h-10 bg-green-50 rounded-xl flex items-center justify-center">
            <Eye className="w-5 h-5 text-green-600" />
          </div>
          <div>
            <p className="text-xl font-bold text-gray-900">{cameras.filter((c: any) => c.is_active).length}</p>
            <p className="text-xs text-gray-500">Online</p>
          </div>
        </div>
        <div className="card flex items-center gap-3">
          <div className="w-10 h-10 bg-red-50 rounded-xl flex items-center justify-center">
            <AlertTriangle className="w-5 h-5 text-red-600" />
          </div>
          <div>
            <p className="text-xl font-bold text-gray-900">{openCount}</p>
            <p className="text-xs text-gray-500">Active Alerts</p>
          </div>
        </div>
        <div className="card flex items-center gap-3">
          <div className="w-10 h-10 bg-purple-50 rounded-xl flex items-center justify-center">
            <Shield className="w-5 h-5 text-purple-600" />
          </div>
          <div>
            <p className="text-xl font-bold text-gray-900">{cameras.filter((c: any) => c.ai_monitoring_enabled).length}</p>
            <p className="text-xs text-gray-500">AI Active</p>
          </div>
        </div>
      </div>

      {scenarios.length > 0 && (
        <div className="card mb-6">
          <h3 className="font-semibold text-gray-900 mb-1">Hotel surveillance checklist</h3>
          <p className="text-xs text-gray-500 mb-4">
            Per-camera enablement and thresholds are stored in <code className="bg-gray-100 px-1 rounded">scenario_rules</code> on each camera.
            Timer-based scenarios (e.g. guard absent at gate) should emit an event after the configured duration.
          </p>
          <div className="max-h-72 overflow-y-auto space-y-2 pr-1">
            {scenarios.map((s: { code: string; label: string; description: string; default_severity: string; is_timer_based: boolean; default_threshold_seconds: number | null; root_cause_hint: string }) => (
              <div key={s.code} className="p-3 rounded-lg bg-gray-50 border border-gray-100 text-sm">
                <div className="flex justify-between gap-2 items-start">
                  <span className="font-medium text-gray-800">{s.label}</span>
                  <Badge variant={s.default_severity === 'critical' ? 'red' : s.default_severity === 'high' ? 'orange' : 'yellow'}>{s.default_severity}</Badge>
                </div>
                <p className="text-xs text-gray-500 mt-1">{s.description}</p>
                {s.is_timer_based && (
                  <p className="text-xs text-blue-600 mt-1">
                    Timer-based — suggested threshold: {s.default_threshold_seconds != null ? `${s.default_threshold_seconds}s` : 'n/a'}
                  </p>
                )}
                <p className="text-xs text-gray-400 mt-1">Root cause: {s.root_cause_hint}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* WiFi Discovery results */}
      {showDiscover && discoveredCams.length > 0 && (
        <div className="card mb-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-900 flex items-center gap-2">
              <Wifi className="w-5 h-5 text-blue-500" />
              Discovered Cameras ({discoveredCams.length})
            </h3>
            <button onClick={() => setShowDiscover(false)} className="text-gray-400 hover:text-gray-600 text-sm">Dismiss</button>
          </div>
          <div className="grid gap-3">
            {discoveredCams.map((cam: any) => (
              <div key={cam.ip} className="flex items-center justify-between p-3 bg-blue-50 rounded-xl border border-blue-100">
                <div>
                  <p className="font-medium text-gray-900 text-sm">{cam.manufacturer} {cam.model}</p>
                  <p className="text-xs text-gray-500">{cam.ip} — {cam.rtsp_url}</p>
                </div>
                <button
                  onClick={() => addCamera.mutate(cam)}
                  className="btn-primary text-xs px-3 py-1 flex items-center gap-1"
                >
                  <Plus className="w-3 h-3" /> Add
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Camera list */}
      <div className="card mb-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-gray-900 flex items-center gap-2">
            <Camera className="w-5 h-5" /> Registered Cameras
          </h3>
        </div>
        {camsLoading ? (
          <p className="text-gray-400 text-sm">Loading...</p>
        ) : cameras.length === 0 ? (
          <p className="text-gray-400 text-sm">No cameras added yet. Use "Discover Cameras" to scan your network.</p>
        ) : (
          <div className="space-y-2">
            {cameras.map((cam: any) => (
              <div key={cam.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${cam.is_active ? 'bg-green-500' : 'bg-gray-300'}`} />
                  <div>
                    <p className="font-medium text-gray-900 text-sm">{cam.name}</p>
                    <p className="text-xs text-gray-500">{cam.location} · {cam.camera_type}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {cam.ai_monitoring_enabled && (
                    <Badge variant="purple">AI</Badge>
                  )}
                  <button
                    onClick={() => toggleAI.mutate(cam.id)}
                    className="p-1.5 rounded-lg hover:bg-gray-200 text-gray-500"
                    title="Toggle AI monitoring"
                  >
                    <Power className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => deleteCamera.mutate(cam.id)}
                    className="p-1.5 rounded-lg hover:bg-red-100 text-red-500"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Alert feed */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-gray-900 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-orange-500" />
            Surveillance Events
          </h3>
          <button onClick={() => refetchEvents()} className="text-gray-400 hover:text-gray-600">
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
        {eventsLoading ? (
          <p className="text-gray-400 text-sm">Loading events...</p>
        ) : events.length === 0 ? (
          <p className="text-gray-400 text-sm">No events recorded.</p>
        ) : (
          <div className="space-y-3">
            {events.map((event: any) => (
              <div
                key={event.id}
                className={`p-4 rounded-xl border-2 ${
                  event.status === 'open' ? 'border-red-100 bg-red-50/50' :
                  event.status === 'acknowledged' ? 'border-yellow-100 bg-yellow-50/50' :
                  'border-gray-100 bg-gray-50/50'
                }`}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-start gap-3">
                    <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${
                      event.severity === 'critical' ? 'bg-red-100' :
                      event.severity === 'high' ? 'bg-orange-100' :
                      event.severity === 'medium' ? 'bg-yellow-100' : 'bg-green-100'
                    }`}>
                      <Camera className={`w-5 h-5 ${
                        event.severity === 'critical' ? 'text-red-600' :
                        event.severity === 'high' ? 'text-orange-600' :
                        event.severity === 'medium' ? 'text-yellow-600' : 'text-green-600'
                      }`} />
                    </div>
                    <div>
                      <p className="font-semibold text-gray-900 text-sm">{event.event_type?.replace(/_/g, ' ')}</p>
                      <p className="text-xs text-gray-500">{event.description}</p>
                      {event.detection_mode === 'duration' && event.duration_seconds != null && (
                        <p className="text-xs text-blue-600 mt-1">
                          Timer: {event.duration_seconds}s / threshold {event.threshold_seconds ?? '?'}s
                          {event.scenario_code ? ` · ${event.scenario_code}` : ''}
                        </p>
                      )}
                      <p className="text-xs text-gray-400 mt-1">
                        {event.detected_at ? new Date(event.detected_at).toLocaleTimeString() : ''}
                      </p>
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-2 flex-shrink-0">
                    <Badge variant={severityColors[event.severity] || 'gray'}>{event.severity}</Badge>
                    <Badge variant={event.status === 'open' ? 'red' : event.status === 'acknowledged' ? 'yellow' : 'green'}>
                      {event.status}
                    </Badge>
                    {event.status === 'open' && (
                      <button
                        onClick={() => ackEvent.mutate({ id: event.id, status: 'acknowledged' })}
                        className="text-xs text-blue-600 hover:underline"
                      >
                        Acknowledge
                      </button>
                    )}
                    {event.status === 'acknowledged' && (
                      <button
                        onClick={() => ackEvent.mutate({ id: event.id, status: 'resolved' })}
                        className="text-xs text-green-600 hover:underline"
                      >
                        Resolve
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
    </RequirePropertyScope>
  )
}
