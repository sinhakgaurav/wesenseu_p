import { useEffect, useRef } from 'react'

type Props = {
  value: string
  onChange: (html: string) => void
  placeholder?: string
  minHeight?: string
}

/**
 * Rich HTML editor (CKEditor 5 when installed, else contenteditable fallback).
 */
export function RichTextEditor({ value, onChange, placeholder, minHeight = '220px' }: Props) {
  const hostRef = useRef<HTMLDivElement>(null)
  const editorRef = useRef<{ destroy: () => void } | null>(null)

  useEffect(() => {
    let cancelled = false

    async function mount() {
      if (!hostRef.current || editorRef.current) return
      try {
        const { CKEditor } = await import('@ckeditor/ckeditor5-react')
        const ClassicEditor = (await import('@ckeditor/ckeditor5-build-classic')).default
        if (cancelled || !hostRef.current) return

        const editor = await ClassicEditor.create(hostRef.current, {
          placeholder: placeholder || 'Write content…',
          toolbar: [
            'heading', '|', 'bold', 'italic', 'link', 'bulletedList', 'numberedList', '|',
            'blockQuote', 'insertTable', '|', 'undo', 'redo',
          ],
        })
        editor.setData(value || '')
        editor.model.document.on('change:data', () => {
          onChange(editor.getData())
        })
        editorRef.current = editor
      } catch {
        // Fallback: contenteditable
        if (!hostRef.current || cancelled) return
        hostRef.current.contentEditable = 'true'
        hostRef.current.className =
          'prose prose-sm max-w-none border border-gray-200 rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white'
        hostRef.current.style.minHeight = minHeight
        hostRef.current.innerHTML = value || ''
        hostRef.current.addEventListener('input', () => onChange(hostRef.current?.innerHTML || ''))
      }
    }

    mount()
    return () => {
      cancelled = true
      if (editorRef.current && 'destroy' in editorRef.current) {
        editorRef.current.destroy()
        editorRef.current = null
      }
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const ed = editorRef.current as { getData?: () => string; setData?: (v: string) => void } | null
    if (ed?.setData && ed.getData?.() !== value) {
      ed.setData(value || '')
    } else if (hostRef.current?.contentEditable === 'true' && hostRef.current.innerHTML !== value) {
      hostRef.current.innerHTML = value || ''
    }
  }, [value])

  return <div ref={hostRef} style={{ minHeight }} className="ckeditor-host" />
}
