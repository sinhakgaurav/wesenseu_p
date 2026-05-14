import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User } from 'lucide-react'
import api from '@/lib/api'
import { PublicNav } from '@/components/layout/PublicNav'

interface Message { role: 'user' | 'assistant'; content: string; ts: Date }

export function SupportChatPage() {
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [starting, setStarting] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  const startConversation = async () => {
    setStarting(true)
    try {
      const session_id = `guest-${Date.now()}`
      const { data } = await api.post('/support/conversations', { subject: 'Website enquiry', session_id })
      setConversationId(data.conversation_id)
      // Load initial greeting
      const conv = await api.get(`/support/conversations/${data.conversation_id}`)
      const msgs: Message[] = (conv.data.messages || []).map((m: any) => ({
        role: m.role as 'assistant' | 'user',
        content: m.content,
        ts: new Date(m.created_at),
      }))
      setMessages(msgs)
    } catch {
      setMessages([{
        role: 'assistant',
        content: "Hi! I'm Monitour's support assistant. How can I help you today?",
        ts: new Date(),
      }])
    } finally {
      setStarting(false)
    }
  }

  useEffect(() => { startConversation() }, [])

  const sendMessage = async () => {
    if (!input.trim() || loading) return
    const text = input.trim()
    setInput('')
    setMessages(m => [...m, { role: 'user', content: text, ts: new Date() }])
    setLoading(true)
    try {
      const { data } = await api.post(`/support/conversations/${conversationId}/messages`, { content: text })
      setMessages(m => [...m, { role: 'assistant', content: data.ai_reply.content, ts: new Date() }])
    } catch {
      setMessages(m => [...m, { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.', ts: new Date() }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 flex flex-col">
      <PublicNav />

      <div className="flex-1 flex items-center justify-center p-6">
        <div className="w-full max-w-2xl bg-white rounded-3xl shadow-xl flex flex-col" style={{ height: '70vh' }}>
          {/* Header */}
          <div className="p-5 border-b border-gray-100 flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center">
              <Bot className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="font-semibold text-gray-900">Monitour Support</p>
              <p className="text-xs text-gray-500">AI-powered · usually replies instantly</p>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-5 space-y-4">
            {starting ? (
              <div className="flex items-center gap-2 text-gray-400 text-sm">
                <div className="w-5 h-5 rounded-full bg-blue-100 flex items-center justify-center">
                  <Bot className="w-3 h-3 text-blue-600" />
                </div>
                <span className="animate-pulse">Connecting...</span>
              </div>
            ) : (
              messages.map((msg, i) => (
                <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  {msg.role === 'assistant' && (
                    <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                      <Bot className="w-4 h-4 text-blue-600" />
                    </div>
                  )}
                  <div className={`max-w-[75%] px-4 py-2.5 rounded-2xl text-sm ${
                    msg.role === 'user'
                      ? 'bg-blue-600 text-white rounded-br-sm'
                      : 'bg-gray-100 text-gray-800 rounded-bl-sm'
                  }`}>
                    {msg.content}
                  </div>
                  {msg.role === 'user' && (
                    <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center flex-shrink-0">
                      <User className="w-4 h-4 text-gray-500" />
                    </div>
                  )}
                </div>
              ))
            )}
            {loading && (
              <div className="flex gap-3 justify-start">
                <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                  <Bot className="w-4 h-4 text-blue-600" />
                </div>
                <div className="bg-gray-100 rounded-2xl rounded-bl-sm px-4 py-2.5 flex gap-1 items-center">
                  <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div className="p-4 border-t border-gray-100">
            <div className="flex gap-3">
              <input
                type="text"
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && sendMessage()}
                placeholder="Ask me anything about Monitour..."
                className="flex-1 bg-gray-50 border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-200"
                disabled={loading || !conversationId}
              />
              <button
                onClick={sendMessage}
                disabled={loading || !input.trim() || !conversationId}
                className="bg-blue-600 text-white rounded-xl px-4 py-2.5 hover:bg-blue-700 disabled:opacity-50"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
            <div className="flex flex-wrap gap-2 mt-2">
              {['Pricing', 'Features', 'Free trial', 'CCTV integration'].map(s => (
                <button
                  key={s}
                  onClick={() => { setInput(s); }}
                  className="text-xs bg-blue-50 text-blue-600 px-3 py-1 rounded-full hover:bg-blue-100"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
