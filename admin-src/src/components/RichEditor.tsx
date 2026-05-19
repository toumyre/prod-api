import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Image from '@tiptap/extension-image'
import Link from '@tiptap/extension-link'
import Placeholder from '@tiptap/extension-placeholder'
import { useRef } from 'react'
import { marked } from 'marked'
import TurndownService from 'turndown'
import { uploadImage } from '../lib/api'

const td = new TurndownService({ headingStyle: 'atx', codeBlockStyle: 'fenced' })

interface Props {
  value: string
  onChange: (md: string) => void
  placeholder?: string
}

export default function RichEditor({ value, onChange, placeholder = 'Commencez à écrire...' }: Props) {
  const imgRef = useRef<HTMLInputElement>(null)
  const mdRef = useRef<HTMLInputElement>(null)

  const editor = useEditor({
    extensions: [
      StarterKit,
      Image,
      Link.configure({ openOnClick: false }),
      Placeholder.configure({ placeholder }),
    ],
    content: String(marked.parse(value || '')),
    onUpdate: ({ editor }) => {
      onChange(td.turndown(editor.getHTML()))
    },
  })

  if (!editor) return null

  const btn = (label: string, active: boolean, action: () => void, title?: string) => (
    <button
      type="button"
      className={`rt-btn${active ? ' active' : ''}`}
      onClick={action}
      title={title}
    >
      {label}
    </button>
  )

  const handleImageFile = async (file: File) => {
    try {
      const url = await uploadImage(file)
      editor.chain().focus().setImage({ src: url }).run()
    } catch { /* silent */ }
  }

  const handleMdImport = (file: File) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      const md = e.target?.result as string
      editor.commands.setContent(String(marked.parse(md || '')))
      onChange(md)
    }
    reader.readAsText(file)
  }

  const handleMdExport = () => {
    const md = td.turndown(editor.getHTML())
    const blob = new Blob([md], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'export.md'
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="rich-editor">
      <div className="rich-toolbar">
        {btn('B', editor.isActive('bold'), () => editor.chain().focus().toggleBold().run(), 'Gras')}
        {btn('I', editor.isActive('italic'), () => editor.chain().focus().toggleItalic().run(), 'Italique')}
        <span className="rt-sep" />
        {btn('H2', editor.isActive('heading', { level: 2 }), () => editor.chain().focus().toggleHeading({ level: 2 }).run())}
        {btn('H3', editor.isActive('heading', { level: 3 }), () => editor.chain().focus().toggleHeading({ level: 3 }).run())}
        <span className="rt-sep" />
        {btn('• Liste', editor.isActive('bulletList'), () => editor.chain().focus().toggleBulletList().run())}
        {btn('1. Liste', editor.isActive('orderedList'), () => editor.chain().focus().toggleOrderedList().run())}
        {btn('" Citation', editor.isActive('blockquote'), () => editor.chain().focus().toggleBlockquote().run())}
        {btn('</> Code', editor.isActive('codeBlock'), () => editor.chain().focus().toggleCodeBlock().run())}
        <span className="rt-sep" />
        <input ref={imgRef} type="file" accept="image/*" style={{ display: 'none' }}
          onChange={(e) => { if (e.target.files?.[0]) { handleImageFile(e.target.files[0]); e.target.value = '' } }} />
        {btn('🖼 Image', false, () => imgRef.current?.click(), 'Insérer une image')}
        <span className="rt-sep" />
        <input ref={mdRef} type="file" accept=".md,.txt" style={{ display: 'none' }}
          onChange={(e) => { if (e.target.files?.[0]) { handleMdImport(e.target.files[0]); e.target.value = '' } }} />
        {btn('↑ .md', false, () => mdRef.current?.click(), 'Importer Markdown')}
        {btn('↓ .md', false, handleMdExport, 'Exporter Markdown')}
      </div>
      <EditorContent editor={editor} className="rich-content" />
    </div>
  )
}
