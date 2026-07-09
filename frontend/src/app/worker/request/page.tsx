'use client'

import { useState } from 'react'

type RequestType = 'pto' | 'sick' | 'swap' | 'vet'

interface RequestHistoryItem {
  id: string
  type: RequestType
  dates: string
  status: 'approved' | 'pending' | 'denied'
  reason?: string
}

function fmtShort(offset: number) {
  const d = new Date(Date.now() + offset * 86400000)
  return `${d.toLocaleString('en-US', {month:'short'})} ${d.getDate()}`
}

const DEMO_HISTORY: RequestHistoryItem[] = [
  { id: 'REQ-001', type: 'pto', dates: `${fmtShort(6)}-${new Date(Date.now()+8*86400000).getDate()}`, status: 'approved', reason: 'Family trip' },
  { id: 'REQ-002', type: 'pto', dates: fmtShort(13), status: 'pending', reason: 'Appointment' },
  { id: 'REQ-003', type: 'sick', dates: fmtShort(-11), status: 'approved' },
  { id: 'REQ-004', type: 'pto', dates: `${fmtShort(26)}-${new Date(Date.now()+30*86400000).getDate()}`, status: 'denied', reason: 'Summer vacation' },
]

export default function WorkerRequestPage() {
  const [activeTab, setActiveTab] = useState<'new' | 'history'>('new')
  const [requestType, setRequestType] = useState<'pto' | 'sick_planned' | 'personal'>('pto')
  const [submitted, setSubmitted] = useState(false)
  const [flexible, setFlexible] = useState(false)

  return (
    <div className="px-5 py-6 space-y-6">
      <h1 className="text-heading-md font-bold">Time Off Requests</h1>

      {/* Tab toggle */}
      <div className="flex bg-surface-raised border border-white/[0.06] rounded-2xl p-1.5 shadow-elevation-1">
        <button
          onClick={() => setActiveTab('new')}
          className={`flex-1 py-2.5 rounded-xl text-body-sm font-medium transition ${
            activeTab === 'new' ? 'bg-brand-600 text-white shadow-brand-glow' : 'text-gray-400'
          }`}
        >
          New Request
        </button>
        <button
          onClick={() => setActiveTab('history')}
          className={`flex-1 py-2.5 rounded-xl text-body-sm font-medium transition ${
            activeTab === 'history' ? 'bg-brand-600 text-white shadow-brand-glow' : 'text-gray-400'
          }`}
        >
          My Requests
        </button>
      </div>

      {activeTab === 'new' && !submitted && (
        <div className="space-y-5">
          {/* Request type selector */}
          <div className="space-y-2.5">
            <label className="text-xs text-gray-500 font-medium uppercase tracking-wide">Request Type</label>
            <div className="grid grid-cols-3 gap-3">
              {[
                { key: 'pto' as const, label: 'PTO', desc: 'Vacation/Personal' },
                { key: 'sick_planned' as const, label: 'Sick', desc: 'Planned Medical' },
                { key: 'personal' as const, label: 'Personal', desc: 'Unpaid Leave' },
              ].map(opt => (
                <button
                  key={opt.key}
                  onClick={() => setRequestType(opt.key)}
                  className={`p-4 rounded-2xl border text-center transition press-scale ${
                    requestType === opt.key
                      ? 'border-brand-500/40 bg-brand-950/50 shadow-brand-glow'
                      : 'border-white/[0.06] bg-surface-raised hover:border-white/[0.12]'
                  }`}
                >
                  <p className="text-body-sm font-medium">{opt.label}</p>
                  <p className="text-[10px] text-gray-500 mt-0.5">{opt.desc}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Date selection */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-gray-500 font-medium block mb-1.5">Start Date</label>
              <input
                type="date"
                defaultValue={new Date(Date.now() + 30*86400000).toISOString().split('T')[0]}
                className="w-full bg-surface-overlay border border-white/[0.06] rounded-xl px-3.5 py-3 text-body-sm text-white"
              />
            </div>
            <div>
              <label className="text-xs text-gray-500 font-medium block mb-1.5">End Date</label>
              <input
                type="date"
                defaultValue={new Date(Date.now() + 34*86400000).toISOString().split('T')[0]}
                className="w-full bg-surface-overlay border border-white/[0.06] rounded-xl px-3.5 py-3 text-body-sm text-white"
              />
            </div>
          </div>

          {/* Duration display */}
          <div className="bg-surface-raised border border-white/[0.06] rounded-2xl p-4 flex items-center justify-between shadow-elevation-1">
            <span className="text-body-sm text-gray-400">Duration:</span>
            <span className="text-body-sm font-semibold">5 days (40h)</span>
          </div>

          {/* Priority */}
          <div>
            <label className="text-xs text-gray-500 font-medium block mb-1.5">Priority Ranking</label>
            <select className="w-full bg-surface-overlay border border-white/[0.06] rounded-xl px-3.5 py-3 text-body-sm text-white">
              <option value="1">Priority 1 - Most important to me</option>
              <option value="2">Priority 2 - Would prefer this</option>
              <option value="3">Priority 3 - Flexible on dates</option>
            </select>
            <p className="text-[10px] text-gray-600 mt-1.5">Higher priority = considered first in holiday auction</p>
          </div>

          {/* Reason */}
          <div>
            <label className="text-xs text-gray-500 font-medium block mb-1.5">Reason (optional)</label>
            <input
              type="text"
              placeholder="e.g., Family vacation, wedding, medical"
              className="w-full bg-surface-overlay border border-white/[0.06] rounded-xl px-3.5 py-3 text-body-sm text-white placeholder:text-gray-600"
            />
          </div>

          {/* Flexibility toggle */}
          <div onClick={() => setFlexible(!flexible)} className="flex items-center justify-between bg-surface-raised border border-white/[0.06] rounded-2xl p-4 cursor-pointer press-scale shadow-elevation-1">
            <div>
              <p className="text-body-sm font-medium">Flexible on dates?</p>
              <p className="text-[10px] text-gray-500 mt-0.5">We'll suggest alternatives if denied</p>
            </div>
            <div className={`w-11 h-6 rounded-full relative transition-colors ${flexible ? 'bg-brand-500' : 'bg-surface-highlight'}`}>
              <div className={`w-5 h-5 rounded-full absolute top-0.5 transition-all shadow-elevation-1 ${flexible ? 'bg-white left-[22px]' : 'bg-gray-400 left-0.5'}`}></div>
            </div>
          </div>

          {/* Coverage check preview */}
          <div className="bg-green-500/10 border border-green-500/20 rounded-2xl p-4 shadow-elevation-1">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-2.5 h-2.5 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-xs text-green-400 font-medium uppercase tracking-wide">Coverage Check: PASS</span>
            </div>
            <p className="text-xs text-gray-400 leading-relaxed">
              Min staffing maintained. 3 spots available on your shift code.
              Advance notice requirement (14 days) met.
            </p>
            <p className="text-xs text-green-400 mt-2 font-medium">
              Likely auto-approved (no manager review needed)
            </p>
          </div>

          {/* Balance impact */}
          <div className="bg-surface-raised border border-white/[0.06] rounded-2xl p-5 space-y-3 shadow-elevation-1">
            <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">Balance Impact</p>
            <div className="flex items-center justify-between text-body-sm">
              <span className="text-gray-400">Current PTO:</span>
              <span className="font-medium">48h (6 days)</span>
            </div>
            <div className="flex items-center justify-between text-body-sm">
              <span className="text-gray-400">This request:</span>
              <span className="text-red-400 font-semibold">-40h (5 days)</span>
            </div>
            <div className="flex items-center justify-between text-body-sm border-t border-white/[0.06] pt-3">
              <span className="text-gray-400">Remaining after:</span>
              <span className="text-yellow-400 font-semibold">8h (1 day)</span>
            </div>
          </div>

          {/* Submit */}
          <button
            onClick={() => setSubmitted(true)}
            className="w-full btn-primary py-3.5 text-body-sm"
          >
            Submit Request
          </button>
        </div>
      )}

      {/* Success state */}
      {activeTab === 'new' && submitted && (
        <div className="space-y-5 py-4">
          <div className="text-center">
            <div className="w-16 h-16 bg-green-500/10 border border-green-500/20 rounded-full flex items-center justify-center mx-auto shadow-elevation-2">
              <svg className="w-8 h-8 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="text-heading-sm font-bold mt-4">Request Auto-Approved!</h2>
            <p className="text-gray-400 text-body-sm mt-2 leading-relaxed">
              Your PTO for Aug 10-14 has been approved automatically.
              Coverage is maintained and all compliance checks passed.
            </p>
          </div>

          {/* Live balance update */}
          <div className="bg-green-500/10 border border-green-500/20 rounded-2xl p-5 shadow-elevation-1">
            <p className="text-xs text-green-400 font-medium uppercase tracking-wide mb-3">Balance Updated</p>
            <div className="grid grid-cols-3 gap-3 text-center">
              <div>
                <p className="text-heading-sm font-bold text-red-400">-40h</p>
                <p className="text-[10px] text-gray-500 mt-0.5">Deducted</p>
              </div>
              <div>
                <p className="text-heading-sm font-bold text-white">8h</p>
                <p className="text-[10px] text-gray-500 mt-0.5">PTO Remaining</p>
              </div>
              <div>
                <p className="text-heading-sm font-bold text-green-400">1 day</p>
                <p className="text-[10px] text-gray-500 mt-0.5">PTO Left</p>
              </div>
            </div>
          </div>

          {/* Confirmation details */}
          <div className="bg-surface-raised border border-white/[0.06] rounded-2xl p-5 text-body-sm space-y-3 shadow-elevation-1">
            <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">Request Details</p>
            <div className="flex justify-between"><span className="text-gray-400">Request ID</span><span className="font-medium">REQ-005</span></div>
            <div className="flex justify-between"><span className="text-gray-400">Status</span><span className="text-green-400 font-semibold">Auto-Approved</span></div>
            <div className="flex justify-between"><span className="text-gray-400">Dates</span><span className="font-medium">Aug 10-14 (5 days)</span></div>
            <div className="flex justify-between"><span className="text-gray-400">PTO deducted</span><span className="font-medium">40h</span></div>
          </div>

          {/* Notifications sent */}
          <div className="bg-surface-raised border border-white/[0.06] rounded-2xl p-5 space-y-4 shadow-elevation-1">
            <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">Notifications Sent</p>
            <div className="flex items-start gap-3">
              <span className="text-green-400 text-lg">&#10003;</span>
              <div>
                <p className="text-body-sm font-medium">You</p>
                <p className="text-xs text-gray-400 mt-0.5 leading-relaxed">"Your PTO for Aug 10-14 is confirmed. Coverage maintained. Enjoy your time off!"</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <span className="text-brand-400 text-lg">&#9993;</span>
              <div>
                <p className="text-body-sm font-medium">Your Manager</p>
                <p className="text-xs text-gray-400 mt-0.5 leading-relaxed">"Sarah Chen PTO auto-approved (Aug 10-14). Coverage OK — no action needed."</p>
              </div>
            </div>
          </div>

          <button
            onClick={() => setSubmitted(false)}
            className="w-full border border-white/[0.1] active:bg-surface-highlight py-3.5 rounded-2xl text-body-sm text-gray-300 transition press-scale"
          >
            Submit Another Request
          </button>
        </div>
      )}

      {/* History tab */}
      {activeTab === 'history' && (
        <div className="space-y-3">
          {DEMO_HISTORY.map(req => (
            <div key={req.id} className="bg-surface-raised border border-white/[0.06] rounded-2xl p-4 shadow-elevation-1 press-card">
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-2.5">
                  <span className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${
                    req.type === 'pto' ? 'bg-cyan-500/15 text-cyan-400' :
                    req.type === 'sick' ? 'bg-orange-500/15 text-orange-400' :
                    'bg-surface-highlight text-gray-400'
                  }`}>
                    {req.type.toUpperCase()}
                  </span>
                  <span className="text-body-sm font-medium">{req.dates}</span>
                </div>
                <span className={`text-xs font-semibold ${
                  req.status === 'approved' ? 'text-green-400' :
                  req.status === 'pending' ? 'text-yellow-400' :
                  'text-red-400'
                }`}>
                  {req.status.charAt(0).toUpperCase() + req.status.slice(1)}
                </span>
              </div>
              {req.reason && (
                <p className="text-xs text-gray-500">{req.reason}</p>
              )}
              <p className="text-[10px] text-gray-600 mt-1.5">{req.id}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
