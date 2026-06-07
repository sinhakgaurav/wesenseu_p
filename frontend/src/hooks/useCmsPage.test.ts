import { describe, it, expect } from 'vitest'
import { htmlFromCmsPage, type CmsPageContent } from './useCmsPage'

describe('htmlFromCmsPage', () => {
  it('returns empty string when page is undefined', () => {
    expect(htmlFromCmsPage(undefined)).toBe('')
  })

  it('extracts html block body', () => {
    const page: CmsPageContent = {
      id: '1',
      slug: 'about',
      title: 'About',
      page_type: 'marketing',
      content_blocks: [{ type: 'html', data: { body: '<p>Hello</p>' } }],
      is_published: true,
    }
    expect(htmlFromCmsPage(page)).toBe('<p>Hello</p>')
  })

  it('returns empty when no html block', () => {
    const page: CmsPageContent = {
      id: '1',
      slug: 'x',
      title: 'X',
      page_type: 'marketing',
      content_blocks: [{ type: 'hero', data: { title: 'Hi' } }],
      is_published: true,
    }
    expect(htmlFromCmsPage(page)).toBe('')
  })
})
