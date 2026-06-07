import type { CmsPageContent } from '@/hooks/useCmsPage'

type Props = {
  page?: CmsPageContent | null
  fallbackTitle: string
  fallbackSubtitle?: string
  className?: string
}

export function CmsPageHero({ page, fallbackTitle, fallbackSubtitle, className = 'bg-gradient-to-br from-indigo-50 to-white pt-20 pb-16' }: Props) {
  const title = page?.hero_heading || page?.title || fallbackTitle
  const subtitle = page?.hero_subheading || fallbackSubtitle

  return (
    <section className={className}>
      <div className="max-w-3xl mx-auto px-6 text-center">
        <h1 className="text-4xl font-extrabold text-gray-900 mb-4">{title}</h1>
        {subtitle && <p className="text-xl text-gray-600">{subtitle}</p>}
      </div>
    </section>
  )
}

export function CmsHtmlBody({ html, className = 'prose prose-gray max-w-3xl mx-auto px-6 py-8' }: { html: string; className?: string }) {
  if (!html?.trim()) return null
  return (
    <section className={className}>
      <div className="cms-html-body" dangerouslySetInnerHTML={{ __html: html }} />
    </section>
  )
}
