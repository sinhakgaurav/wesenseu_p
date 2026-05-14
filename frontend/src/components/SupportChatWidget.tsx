import { useState, useRef, useEffect } from 'react'
import { Bot, User, Send, X, Minus, MessageCircle, Sparkles } from 'lucide-react'
import api from '@/lib/api'

interface Message {
  role: 'user' | 'assistant'
  content: string
  ts: Date
}

const QUICK_REPLIES = ['Pricing', 'Features', 'Free trial', 'CCTV setup', 'Room AI']

export function SupportChatWidget() {
  const [open, setOpen] = useState(false)
  const [minimised, setMinimised] = useState(false)
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [starting, setStarting] = useState(false)
  const [unread, setUnread] = useState(0)
  const [showPulse, setShowPulse] = useState(true)
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Scroll to bottom whenever messages change
  useEffect(() => {
    if (open && !minimised) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, open, minimised])

  // Stop pulse after 6 seconds
  useEffect(() => {
    const t = setTimeout(() => setShowPulse(false), 6000)
    return () => clearTimeout(t)
  }, [])

  // Track unread messages while closed
  useEffect(() => {
    if (!open) {
      const assistantMsgs = messages.filter(m => m.role === 'assistant').length
      if (assistantMsgs > 0 && conversationId) setUnread(1)
    } else {
      setUnread(0)
    }
  }, [messages, open])

  // Focus input when opening
  useEffect(() => {
    if (open && !minimised) {
      setTimeout(() => inputRef.current?.focus(), 100)
    }
  }, [open, minimised])

  const startConversation = async () => {
    if (conversationId) return
    setStarting(true)
    try {
      const { data } = await api.post('/support/conversations', {
        subject: 'Website enquiry',
        session_id: `widget-${Date.now()}`,
      })
      setConversationId(data.conversation_id)
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
        content: "Hi! I'm Monitour's support assistant. Ask me about pricing, features, CCTV, or anything else!",
        ts: new Date(),
      }])
    } finally {
      setStarting(false)
    }
  }

  const handleOpen = () => {
    setOpen(true)
    setMinimised(false)
    setUnread(0)
    startConversation()
  }

  const sendMessage = async (text?: string) => {
    const msg = (text ?? input).trim()
    if (!msg || loading) return
    setInput('')
    setMessages(m => [...m, { role: 'user', content: msg, ts: new Date() }])
    setLoading(true)
    try {
      const id = conversationId
      const { data } = await api.post(`/support/conversations/${id}/messages`, { content: msg })
      setMessages(m => [...m, { role: 'assistant', content: data.ai_reply.content, ts: new Date() }])
    } catch {
      setMessages(m => [...m, {
        role: 'assistant',
        content: 'Sorry, something went wrong. Please email support@monitour.in',
        ts: new Date(),
      }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      {/* Chat panel */}
      {open && (
        <div
          className={`fixed bottom-24 right-5 z-50 flex flex-col bg-white rounded-2xl shadow-2xl border border-gray-100 transition-all duration-300 ${
            minimised ? 'h-14 w-72 overflow-hidden' : 'w-80 sm:w-96'
          }`}
          style={{ maxHeight: minimised ? '56px' : '520px' }}
        >
          {/* Header */}
          <div className="flex items-center gap-3 px-4 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-t-2xl flex-shrink-0">
            <div className="relative">
              <div className="w-9 h-9 bg-white/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-400 border-2 border-white rounded-full" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-white font-semibold text-sm leading-tight">Monitour Support</p>
              <p className="text-blue-100 text-xs truncate">AI-powered · replies instantly</p>
            </div>
            <div className="flex items-center gap-1">
              <button
                onClick={() => setMinimised(v => !v)}
                className="p-1.5 rounded-lg hover:bg-white/20 text-white/80 hover:text-white transition-colors"
                title={minimised ? 'Expand' : 'Minimise'}
              >
                <Minus className="w-4 h-4" />
              </button>
              <button
                onClick={() => setOpen(false)}
                className="p-1.5 rounded-lg hover:bg-white/20 text-white/80 hover:text-white transition-colors"
                title="Close"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {!minimised && (
            <>
              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-gray-50/50" style={{ minHeight: 0 }}>
                {starting ? (
                  <div className="flex items-center gap-2 text-gray-400 text-sm py-4 justify-center">
                    <div className="w-4 h-4 border-2 border-blue-300 border-t-blue-600 rounded-full animate-spin" />
                    <span>Connecting...</span>
                  </div>
                ) : (
                  messages.map((msg, i) => (
                    <div key={i} className={`flex gap-2 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                      {msg.role === 'assistant' && (
                        <div className="w-7 h-7 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                          <Bot className="w-3.5 h-3.5 text-blue-600" />
                        </div>
                      )}
                      <div className={`max-w-[80%] px-3 py-2 rounded-2xl text-sm leading-relaxed ${
                        msg.role === 'user'
                          ? 'bg-blue-600 text-white rounded-br-sm'
                          : 'bg-white text-gray-800 rounded-bl-sm shadow-sm border border-gray-100'
                      }`}>
                        {msg.content}
                      </div>
                      {msg.role === 'user' && (
                        <div className="w-7 h-7 bg-gray-200 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                          <User className="w-3.5 h-3.5 text-gray-500" />
                        </div>
                      )}
                    </div>
                  ))
                )}

                {loading && (
                  <div className="flex gap-2 justify-start">
                    <div className="w-7 h-7 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                      <Bot className="w-3.5 h-3.5 text-blue-600" />
                    </div>
                    <div className="bg-white rounded-2xl rounded-bl-sm px-4 py-3 flex gap-1 items-center shadow-sm border border-gray-100">
                      <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                  </div>
                )}
                <div ref={bottomRef} />
              </div>

              {/* Quick replies */}
              {messages.length <= 2 && !loading && (
                <div className="px-4 pt-2 pb-0 flex flex-wrap gap-1.5">
                  {QUICK_REPLIES.map(s => (
                    <button
                      key={s}
                      onClick={() => sendMessage(s)}
                      disabled={loading || !conversationId}
                      className="text-xs bg-blue-50 text-blue-600 border border-blue-100 px-2.5 py-1 rounded-full hover:bg-blue-100 transition-colors disabled:opacity-50"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              )}

              {/* Input */}
              <div className="p-3 border-t border-gray-100 bg-white rounded-b-2xl flex-shrink-0">
                <div className="flex gap-2">
                  <input
                    ref={inputRef}
                    type="text"
                    value={input}
                    onChange={e => setInput(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendMessage()}
                    placeholder="Type a message..."
                    disabled={loading || !conversationId}
                    className="flex-1 bg-gray-50 border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-200 disabled:opacity-50"
                  />
                  <button
                    onClick={() => sendMessage()}
                    disabled={loading || !input.trim() || !conversationId}
                    className="bg-blue-600 text-white rounded-xl px-3 py-2 hover:bg-blue-700 disabled:opacity-40 transition-colors flex-shrink-0"
                  >
                    <Send className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {/* Floating trigger button */}
      <div className="fixed bottom-5 right-5 z-50 flex flex-col items-end gap-3">
        {/* Tooltip hint (shows briefly on load) */}
        {showPulse && !open && (
          <div className="bg-gray-900 text-white text-xs rounded-xl px-3 py-2 shadow-lg flex items-center gap-2 animate-fade-in">
            <Sparkles className="w-3.5 h-3.5 text-yellow-400 flex-shrink-0" />
            <span>Need help? Chat with us!</span>
          </div>
        )}

        <button
          onClick={open ? () => setOpen(false) : handleOpen}
          className="relative w-14 h-14 bg-gradient-to-br from-blue-600 to-indigo-600 text-white rounded-2xl shadow-lg hover:shadow-xl hover:scale-105 active:scale-95 transition-all duration-200 flex items-center justify-center"
          aria-label="Support chat"
        >
          {open ? (
            <X className="w-6 h-6" />
          ) : (
            <MessageCircle className="w-6 h-6" />
          )}

          {/* Unread badge */}
          {!open && unread > 0 && (
            <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs font-bold rounded-full flex items-center justify-center border-2 border-white">
              {unread}
            </span>
          )}

          {/* Pulse ring on first load */}
          {!open && showPulse && (
            <span className="absolute inset-0 rounded-2xl bg-blue-500 animate-ping opacity-30" />
          )}
        </button>
      </div>
    </>
  )
}
