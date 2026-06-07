import { useState, useRef, useMemo, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Image, Upload, Trash2, Plus } from 'lucide-react'
import api from '@/lib/api'
import toast from 'react-hot-toast'
import { useAdminPropertyId } from '@/hooks/useAdminPropertyId'
import { RequirePropertyScope } from '@/components/layout/RequirePropertyScope'

type BenchmarkRow = {
  id: string
  property_id: string
  property_room_category_id?: string | null
  room_category: string
  aspect: string
  image_url: string
  thumbnail_url?: string | null
  description?: string | null
}

type CategoryRow = { key: string; label: string; managedId?: string; legacyName?: string; count: number }

function parseBenchmarkCategoriesResponse(data: unknown): CategoryRow[] {
  if (!data) return []
  if (Array.isArray(data)) {
    return data.map((c: { room_category?: string; benchmark_count?: number }) => ({
      key: `legacy:${c.room_category}`,
      label: c.room_category || 'Unknown',
      legacyName: c.room_category,
      count: Number(c.benchmark_count ?? 0),
    }))
  }
  const d = data as { managed?: Array<{ property_room_category_id: string; code: string | null; display_name: string; benchmark_count: number }>; legacy_string_only?: Array<{ room_category: string; benchmark_count: number }> }
  const managed = (d.managed ?? []).map((m) => ({
    key: `managed:${m.property_room_category_id}`,
    label: m.display_name,
    managedId: m.property_room_category_id,
    count: m.benchmark_count,
  }))
  const legacy = (d.legacy_string_only ?? []).map((r) => ({
    key: `legacy:${r.room_category}`,
    label: r.room_category,
    legacyName: r.room_category,
    count: r.benchmark_count,
  }))
  return [...managed, ...legacy]
}

export function BenchmarksPage() {
  const { propertyId, enabled } = useAdminPropertyId()
  const qc = useQueryClient()
  const fileRef = useRef<HTMLInputElement>(null)
  const [selectedKey, setSelectedKey] = useState('')
  const [selectedAspect, setSelectedAspect] = useState('general')
  const [customAspect, setCustomAspect] = useState('')
  const [description, setDescription] = useState('')
  const [uploading, setUploading] = useState(false)

  const { data: rawCategories } = useQuery({
    queryKey: ['benchmark-categories', propertyId],
    queryFn: () =>
      api.get(`/benchmarks/categories${propertyId ? `?property_id=${propertyId}` : ''}`).then((r) => r.data),
  })

  const categoryRows = useMemo(() => parseBenchmarkCategoriesResponse(rawCategories), [rawCategories])

  useEffect(() => {
    if (!selectedKey && categoryRows.length) setSelectedKey(categoryRows[0].key)
  }, [categoryRows, selectedKey])

  const { data: aspectsList = [] } = useQuery({
    queryKey: ['benchmark-aspects'],
    queryFn: () => api.get('/room-categories/suggested-aspects').then((r) => (r.data?.aspects as string[]) ?? []),
  })

  const aspectOptions = useMemo(() => {
    const s = new Set<string>(aspectsList)
    if (customAspect.trim()) s.add(customAspect.trim())
    s.add('general')
    return Array.from(s)
  }, [aspectsList, customAspect])

  const selected = useMemo(() => categoryRows.find((c) => c.key === selectedKey), [categoryRows, selectedKey])

  const { data: benchmarks = [] } = useQuery<BenchmarkRow[]>({
    queryKey: ['benchmarks', propertyId, selectedKey],
    enabled: enabled && !!selectedKey,
    queryFn: async () => {
      const params = new URLSearchParams()
      if (propertyId) params.set('property_id', propertyId)
      if (selected?.managedId) params.set('property_room_category_id', selected.managedId)
      else if (selected?.legacyName) params.set('room_category', selected.legacyName)
      const { data } = await api.get(`/benchmarks?${params}`)
      return data
    },
  })

  const deleteBenchmark = useMutation({
    mutationFn: (id: string) => api.delete(`/benchmarks/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['benchmarks'] })
      qc.invalidateQueries({ queryKey: ['benchmark-categories'] })
      toast.success('Benchmark removed')
    },
  })

  const effectiveAspect = customAspect.trim() || selectedAspect

  const handleUpload = async () => {
    const file = fileRef.current?.files?.[0]
    if (!file || !propertyId || !selected) return
    setUploading(true)
    const form = new FormData()
    form.append('file', file)
    form.append('property_id', propertyId)
    form.append('aspect', effectiveAspect)
    if (description) form.append('description', description)
    if (selected.managedId) {
      form.append('property_room_category_id', selected.managedId)
    } else if (selected.legacyName) {
      form.append('room_category', selected.legacyName)
    }
    try {
      await api.post('/benchmarks', form, { headers: { 'Content-Type': 'multipart/form-data' } })
      toast.success('Benchmark image uploaded!')
      qc.invalidateQueries({ queryKey: ['benchmarks'] })
      qc.invalidateQueries({ queryKey: ['benchmark-categories'] })
      setDescription('')
      if (fileRef.current) fileRef.current.value = ''
    } catch {
      toast.error('Upload failed')
    } finally {
      setUploading(false)
    }
  }

  return (
    <RequirePropertyScope>
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Benchmark Images</h1>
          <p className="text-gray-500 text-sm">
            Reference images per room category and aspect (from your property&apos;s category catalog + any legacy names).
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="card lg:col-span-1">
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Upload className="w-5 h-5 text-blue-500" /> Upload benchmark
          </h3>
          <div className="space-y-3">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Room category</label>
              <select
                value={selectedKey}
                onChange={(e) => setSelectedKey(e.target.value)}
                className="input-field w-full"
              >
                {categoryRows.map((c) => (
                  <option key={c.key} value={c.key}>
                    {c.label} ({c.count})
                  </option>
                ))}
              </select>
              {categoryRows.length === 0 && (
                <p className="text-xs text-amber-600 mt-1">Define room categories under Setup → Room Categories.</p>
              )}
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Aspect (preset)</label>
              <select
                value={selectedAspect}
                onChange={(e) => setSelectedAspect(e.target.value)}
                className="input-field w-full"
              >
                {aspectOptions.map((a) => (
                  <option key={a} value={a}>
                    {a}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Custom aspect (optional)</label>
              <input
                className="input-field w-full text-sm"
                value={customAspect}
                onChange={(e) => setCustomAspect(e.target.value)}
                placeholder="Overrides preset when filled, e.g. sidetable"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Description (optional)</label>
              <input
                type="text"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="input-field w-full"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Image file</label>
              <input ref={fileRef} type="file" accept="image/*" className="input-field w-full text-sm" />
            </div>
            <button
              type="button"
              onClick={handleUpload}
              disabled={uploading || !propertyId || !selectedKey}
              className="btn-primary w-full flex items-center justify-center gap-2"
            >
              <Plus className="w-4 h-4" />
              {uploading ? 'Uploading…' : 'Upload benchmark'}
            </button>
          </div>

          <div className="mt-6">
            <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Coverage</h4>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {categoryRows.map((c) => (
                <button
                  key={c.key}
                  type="button"
                  onClick={() => setSelectedKey(c.key)}
                  className={`w-full flex items-center justify-between p-2 rounded-lg text-sm ${
                    selectedKey === c.key ? 'bg-blue-50 border border-blue-200' : 'hover:bg-gray-50'
                  }`}
                >
                  <span className="font-medium truncate text-left">{c.label}</span>
                  <span className="text-gray-500 text-xs flex-shrink-0">{c.count}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-900">
              {selected?.label ?? 'Category'} benchmarks
            </h3>
            <span className="text-sm text-gray-500">{benchmarks.length} images</span>
          </div>
          {benchmarks.length === 0 ? (
            <div className="card text-center py-12">
              <Image className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500 text-sm">No benchmark images for this selection yet.</p>
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-4">
              {benchmarks.map((b) => (
                <div key={b.id} className="card overflow-hidden p-0">
                  <div className="relative bg-gray-100 aspect-video flex items-center justify-center">
                    {b.image_url ? (
                      <img src={b.image_url} alt={b.description || ''} className="w-full h-full object-cover" />
                    ) : (
                      <Image className="w-12 h-12 text-gray-300" />
                    )}
                    <div className="absolute top-2 right-2">
                      <span className="bg-white/90 text-xs font-medium px-2 py-0.5 rounded-full border">{b.aspect}</span>
                    </div>
                  </div>
                  <div className="p-3 flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-900">{b.room_category}</p>
                      {b.description && <p className="text-xs text-gray-500">{b.description}</p>}
                    </div>
                    <button
                      type="button"
                      onClick={() => deleteBenchmark.mutate(b.id)}
                      className="p-1.5 rounded-lg hover:bg-red-100 text-red-400"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
    </RequirePropertyScope>
  )
}
