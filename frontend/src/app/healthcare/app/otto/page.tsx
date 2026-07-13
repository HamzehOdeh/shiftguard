'use client'

import { useState, useRef, useEffect } from 'react'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

const SUGGESTIONS = [
  'Is Dr. Chen safe to cover tonight?',
  'Who has the most night shifts?',
  'Can Dr. Kim moonlight this weekend?',
  'Show duty hours for all PGY-1s',
  "Who's jeopardy backup tomorrow?",
  'Generate next month\'s call schedule',
]

export default function OttoPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  async function sendMessage(text: string) {
    const userMsg: Message = { role: 'user', content: text }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text }),
      })
      const data = await res.json()
      const response = data.message || 'Sorry, I couldn\'t process that.'
      setMessages(prev => [...prev, { role: 'assistant', content: response }])
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Connection error — please try again.' }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Chat area */}
      <div className="flex-1 overflow-y-auto px-4 py-5 space-y-4">
        {messages.length === 0 && (
          <div className="space-y-5">
            <div className="text-center py-4">
              <div className="w-16 h-16 bg-brand-500/15 border border-brand-500/20 rounded-full flex items-center justify-center mx-auto mb-3">
                <span className="text-3xl">ðŸ¤–</span>
              </div>
              <h2 className="text-heading-sm font-bold">Hi, I'm Otto</h2>
              <p className="text-body-sm text-gray-300 mt-1">Your AI scheduling assistant. Ask me anything about duty hours, coverage, or scheduling.</p>
            </div>

            <div className="grid grid-cols-1 gap-2">
              {SUGGESTIONS.map((s, i) => (
                <button
                  key={i}
                  onClick={() => sendMessage(s)}
                  className="text-left bg-gray-800/80 border border-gray-700 rounded-xl px-4 py-3 text-body-sm text-gray-200 hover:border-brand-500/30 transition press-scale"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[85%] rounded-2xl px-4 py-3 ${
              msg.role === 'user'
                ? 'bg-brand-600 text-white'
                : 'bg-gray-800/80 border border-gray-700'
            }`}>
              <p className="text-body-sm whitespace-pre-line">{msg.content}</p>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-800/80 border border-gray-700 rounded-2xl px-4 py-3">
              <div className="flex gap-1.5">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0ms'}}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '150ms'}}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '300ms'}}></div>
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-700 bg-gray-800/80 px-4 py-3 pb-safe">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && input.trim()) sendMessage(input.trim()) }}
            placeholder="Ask Otto anything..."
            className="flex-1 bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-body-sm text-white placeholder:text-gray-500"
          />
          <button
            onClick={() => { if (input.trim()) sendMessage(input.trim()) }}
            className="btn-primary px-5 py-3 text-body-sm"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  )
}

