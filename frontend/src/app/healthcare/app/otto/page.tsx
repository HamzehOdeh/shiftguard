'use client'

import { useState } from 'react'

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

const DEMO_RESPONSES: Record<string, string> = {
  'Is Dr. Chen safe to cover tonight?': "NO — Dr. Chen is at 74h this week (4-week avg: 71h). Adding a 12h night shift would push them to 86h, violating the ACGME 80h cap. Fatigue score is 68/100 (HIGH).\n\nRecommend: Dr. Santos (45h, fatigue 18/100) or Dr. Reeves (58h, fatigue 32/100) — both ACGME-safe.",
  'Who has the most night shifts?': "This month's night shift distribution:\n\n1. Dr. Kim — 6 nights (highest)\n2. Dr. Patel — 5 nights\n3. Dr. Chen — 5 nights\n4. Dr. Reeves — 4 nights\n5. Dr. Santos — 3 nights (lowest, PGY-1)\n\nDr. Kim is approaching the ACGME 6-consecutive-night limit. Next night assignment should go to Dr. Santos or Dr. Reeves for fairness.",
  'Can Dr. Kim moonlight this weekend?': "CONDITIONAL — Dr. Kim is at 71h this week. Moonlighting counts toward the 80h ACGME cap.\n\n• 8h moonlighting shift → 79h total = SAFE (barely)\n• 12h moonlighting shift → 83h total = VIOLATION\n\nApproved for up to 9 hours only. Program Director sign-off required per policy.",
  'Show duty hours for all PGY-1s': "PGY-1 Duty Hours (current week):\n\n• Dr. Santos — 45h / 80h cap (56% utilized)\n  - Fatigue: 18/100 (LOW)\n  - Consecutive days: 3\n  - Status: SAFE\n\nDr. Santos is the only PGY-1 in the program. Well within all ACGME limits. Available for additional coverage if needed.",
  "Who's jeopardy backup tomorrow?": "Tomorrow's jeopardy backup: Dr. Reeves (PGY-2)\n\n• Current hours: 58h (22h remaining before cap)\n• Fatigue: 32/100 (LOW)\n• Last jeopardy activation: 12 days ago\n• ACGME status: SAFE for activation\n\nIf activated, Dr. Reeves would reach ~70h — still well under the 80h cap.",
  "Generate next month's call schedule": "I'll generate a fair call schedule for August. Here's the distribution:\n\n• 31 days × 1 night resident = 31 night shifts needed\n• 5 residents available\n• Target: ~6 nights each\n\nProposed:\n- Dr. Patel: 7 nights (includes 1 weekend)\n- Dr. Kim: 6 nights\n- Dr. Chen: 6 nights\n- Dr. Reeves: 6 nights\n- Dr. Santos: 6 nights\n\nFairness score: EXCELLENT (max deviation: 1 shift). No ACGME violations. Golden weekends preserved for all residents.\n\nWant me to adjust anything?",
}

export default function OttoPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  function sendMessage(text: string) {
    const userMsg: Message = { role: 'user', content: text }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)

    setTimeout(() => {
      const response = DEMO_RESPONSES[text] || `Based on the current schedule data, I can help with that. The residents are all within ACGME limits today. Dr. Chen is closest to the cap at 74h/80h. Would you like me to check something specific about "${text}"?`
      setMessages(prev => [...prev, { role: 'assistant', content: response }])
      setLoading(false)
    }, 800)
  }

  return (
    <div className="flex flex-col h-full">
      {/* Chat area */}
      <div className="flex-1 overflow-y-auto px-4 py-5 space-y-4">
        {messages.length === 0 && (
          <div className="space-y-5">
            <div className="text-center py-4">
              <div className="w-16 h-16 bg-brand-500/15 border border-brand-500/20 rounded-full flex items-center justify-center mx-auto mb-3">
                <span className="text-3xl">🤖</span>
              </div>
              <h2 className="text-heading-sm font-bold">Hi, I'm Otto</h2>
              <p className="text-body-sm text-gray-300 mt-1">Your AI scheduling assistant. Ask me anything about duty hours, coverage, or scheduling.</p>
            </div>

            <div className="grid grid-cols-1 gap-2">
              {SUGGESTIONS.map((s, i) => (
                <button
                  key={i}
                  onClick={() => sendMessage(s)}
                  className="text-left bg-surface-raised border border-white/[0.06] rounded-xl px-4 py-3 text-body-sm text-gray-200 hover:border-brand-500/30 transition press-scale"
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
                : 'bg-surface-raised border border-white/[0.06]'
            }`}>
              <p className="text-body-sm whitespace-pre-line">{msg.content}</p>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-surface-raised border border-white/[0.06] rounded-2xl px-4 py-3">
              <div className="flex gap-1.5">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0ms'}}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '150ms'}}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '300ms'}}></div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="border-t border-white/[0.06] bg-surface-raised px-4 py-3 pb-safe">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && input.trim()) sendMessage(input.trim()) }}
            placeholder="Ask Otto anything..."
            className="flex-1 bg-surface-overlay border border-white/[0.06] rounded-xl px-4 py-3 text-body-sm text-white placeholder:text-gray-500"
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
