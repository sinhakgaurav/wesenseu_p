import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'

export type CmsPageContent = {
  id: string
  slug: string
  title: string
  page_type: string
  hero_heading?: string
  hero_subheading?: string
  hero_image_url?: string
  content_blocks: { type: string; data: Record<string, unknown> }[]
  is_published: boolean
}

export function htmlFromCmsPage(page: CmsPageContent | undefined): string {
  if (!page?.content_blocks?.length) return ''
  const html = page.content_blocks.find((b) => b.type === 'html')
  return (html?.data?.body as string) || ''
}

export function useCmsPage(slug: string) {
  return useQuery<CmsPageContent | null>({
    queryKey: ['cms-page', slug],
    queryFn: async () => {
      try {
        const { data } = await api.get(`/pages/slug/${slug}`)
        return data
      } catch {
        return null
      }
    },
    staleTime: 60_000,
  })
}
