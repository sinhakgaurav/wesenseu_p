import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import toast from 'react-hot-toast'
import { RichTextEditor } from '@/components/ui/RichTextEditor'
import { Badge } from '@/components/ui/Badge'

type CmsPage = {
  id: string
  slug: string
  title: string
  page_type: string
  hero_heading?: string
  hero_subheading?: string
  content_blocks: { type: string; data: Record<string, unknown> }[]
  is_published: boolean
}

const PAGE_TYPES = ['about', 'contact', 'pricing', 'terms', 'privacy', 'blog', 'faq', 'custom']

function htmlFromBlocks(blocks: CmsPage['content_blocks']): string {
  const html = blocks?.find((b) => b.type === 'html')
  return (html?.data?.body as string) || ''
}

function blocksWithHtml(blocks: CmsPage['content_blocks'], body: string) {
  const rest = (blocks || []).filter((b) => b.type !== 'html')
  return [...rest, { type: 'html', data: { body } }]
}

export function SuperAdminCmsTab() {
  const qc = useQueryClient()
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const { data: pages = [], isLoading } = useQuery<CmsPage[]>({
    queryKey: ['cms-pages-admin'],
    queryFn: () => api.get('/pages/admin/all').then((r) => r.data),
  })

  const [draft, setDraft] = useState<Partial<CmsPage>>({})

  useEffect(() => {
    if (!pages.length) return
    const p = pages.find((x) => x.id === selectedId) || pages[0]
    if (p) {
      setDraft({ ...p, content_blocks: p.content_blocks || [] })
      if (!selectedId) setSelectedId(p.id)
    }
  }, [pages, selectedId])

  const savePage = useMutation({
    mutationFn: () => {
      if (!draft.id) return Promise.reject()
      return api.patch(`/pages/${draft.id}`, {
        title: draft.title,
        hero_heading: draft.hero_heading,
        hero_subheading: draft.hero_subheading,
        content_blocks: draft.content_blocks,
        page_type: draft.page_type,
      })
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['cms-pages-admin'] })
      toast.success('Page saved')
    },
  })

  const createPage = useMutation({
    mutationFn: () =>
      api.post('/pages', {
        slug: `page-${Date.now()}`,
        title: 'New Page',
        page_type: 'custom',
        content_blocks: [{ type: 'html', data: { body: '<p></p>' } }],
      }),
    onSuccess: (r) => {
      qc.invalidateQueries({ queryKey: ['cms-pages-admin'] })
      setSelectedId(r.data.id)
      setDraft({ ...r.data, content_blocks: r.data.content_blocks || [] })
      toast.success('Page created')
    },
  })

  const publish = useMutation({
    mutationFn: (id: string) => api.post(`/pages/${id}/publish`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['cms-pages-admin'] })
      toast.success('Published')
    },
  })

  if (isLoading) return <p className="text-gray-400 text-sm">Loading pages…</p>

  const bodyHtml = htmlFromBlocks(draft.content_blocks || [])

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
      <div className="lg:col-span-1 space-y-2">
        <button type="button" className="btn-primary w-full text-sm" onClick={() => createPage.mutate()}>
          New page
        </button>
        {pages.map((p) => (
          <button
            key={p.id}
            type="button"
            onClick={() => { setSelectedId(p.id); setDraft({ ...p, content_blocks: p.content_blocks || [] }) }}
            className={`w-full text-left p-3 rounded-lg border text-sm ${
              selectedId === p.id || (!selectedId && p.id === pages[0]?.id)
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-100 hover:bg-gray-50'
            }`}
          >
            <p className="font-medium text-gray-900">{p.title}</p>
            <p className="text-xs text-gray-500">/{p.slug}</p>
            {p.is_published && <Badge variant="green" className="mt-1">live</Badge>}
          </button>
        ))}
      </div>

      {draft.id && (
        <div className="lg:col-span-3 card space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <input className="input" value={draft.title || ''} onChange={(e) => setDraft({ ...draft, title: e.target.value })} placeholder="Title" />
            <select className="input" value={draft.page_type || 'custom'} onChange={(e) => setDraft({ ...draft, page_type: e.target.value })}>
              {PAGE_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
            <input className="input" value={draft.hero_heading || ''} onChange={(e) => setDraft({ ...draft, hero_heading: e.target.value })} placeholder="Hero heading" />
            <input className="input" value={draft.hero_subheading || ''} onChange={(e) => setDraft({ ...draft, hero_subheading: e.target.value })} placeholder="Hero subheading" />
          </div>

          <div>
            <label className="text-sm font-medium text-gray-700 mb-2 block">Page body (rich HTML)</label>
            <RichTextEditor
              value={bodyHtml}
              onChange={(html) =>
                setDraft({
                  ...draft,
                  content_blocks: blocksWithHtml(draft.content_blocks || [], html),
                })
              }
            />
          </div>

          <div className="flex gap-2">
            <button type="button" className="btn-primary" onClick={() => savePage.mutate()} disabled={savePage.isPending}>
              Save
            </button>
            <button type="button" className="btn-secondary" onClick={() => draft.id && publish.mutate(draft.id)}>
              Publish
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
