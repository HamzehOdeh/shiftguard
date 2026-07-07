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

const DEMO_HISTORY: RequestHistoryItem[] = [
  { id: 'REQ-001', type: 'pto', dates: 'Jul 15-17', status: 'approved', reason: 'Family trip' },
  { id: 'REQ-002', type: 'pto', dates: 'Jul 22', status: 'pending', reason: 'Appointment' },
  { id: 'REQ-003', type: 'sick', dates: 'Jun 28', status: 'approved' },
  { id: 'REQ-004', type: 'pto', dates: 'Aug 4-8', status: 'denied', reason: 'Summer vacation' },
]

export default function WorkerRequestPage() {
  const [activeTab, setActiveTab] = useState<'new' | 'history'>('new')
  const [requestType, setRequestType] = useState<'pto' | 'sick_planned' | 'personal'>('pto')
  const [submitted, setSubmitted] = useState(false)

  return (
    <div className="px-4 py-5 space-y-4">
      <h1 className="text-xl font-bold">Time Off Requests</h1>

      {/* Tab toggle */}
      <div className="flex bg-gray-900 rounded-lg p-1">
        <button
          onClick={() => setActiveTab('new')}
          className={`flex-1 py-2 rounded-md text-sm font-medium transition ${
            activeTab === 'new' ? 'bg-brand-600 text-white' : 'text-gray-400'
          }`}
        >
          New Request
        </button>
        <button
          onClick={() => setActiveTab('history')}
          className={`flex-1 py-2 rounded-md text-sm font-medium transition ${
            activeTab === 'history' ? 'bg-brand-600 text-white' : 'text-gray-400'
          }`}
        >
          My Requests
        </button>
      </div>

      {activeTab === 'new' && !submitted && (
        <div className="space-y-4">
          {/* Request type selector */}
          <div className="space-y-2">
            <label className="text-xs text-gray-500 font-medium uppercase">Request Type</label>
            <div className="grid grid-cols-3 gap-2">
              {[
                { key: 'pto' as const, label: 'PTO', desc: 'Vacation/Personal' },
                { key: 'sick_planned' as const, label: 'Sick', desc: 'Planned Medical' },
                { key: 'personal' as const, label: 'Personal', desc: 'Unpaid Leave' },
              ].map(opt => (
                <button
                  key={opt.key}
                  onClick={() => setRequestType(opt.key)}
                  className={`p-3 rounded-lg border text-center transition ${
                    requestType === opt.key
                      ? 'border-brand-500 bg-brand-950'
                      : 'border-gray-700 bg-gray-900 hover:border-gray-500'
                  }`}
                >
                  <p className="text-sm font-medium">{opt.label}</p>
                  <p className="text-[10px] text-gray-500">{opt.desc}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Date selection */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-gray-500 font-medium block mb-1">Start Date</label>
              <input
                type="date"
                defaultValue="2026-08-10"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2.5 text-sm text-white"
              />
            </div>
            <div>
              <label className="text-xs text-gray-500 font-medium block mb-1">End Date</label>
              <input
                type="date"
                defaultValue="2026-08-14"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2.5 text-sm text-white"
              />
            </div>
          </div>

          {/* Duration display */}
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-3 flex items-center justify-between">
            <span className="text-sm text-gray-400">Duration:</span>
            <span className="text-sm font-medium">5 days (40h)</span>
          </div>

          {/* Priority */}
          <div>
            <label className="text-xs text-gray-500 font-medium block mb-1">Priority Ranking</label>
            <select className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2.5 text-sm text-white">
              <option value="1">Priority 1 - Most important to me</option>
              <option value="2">Priority 2 - Would prefer this</option>
              <option value="3">Priority 3 - Flexible on dates</option>
            </select>
            <p className="text-[10px] text-gray-600 mt-1">Higher priority = considered first in holiday auction</p>
          </div>

          {/* Reason */}
          <div>
            <label className="text-xs text-gray-500 font-medium block mb-1">Reason (optional)</label>
            <input
              type="text"
              placeholder="e.g., Family vacation, wedding, medical"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2.5 text-sm text-white placeholder:text-gray-600"
            />
          </div>

          {/* Flexibility toggle */}
          <div className="flex items-center justify-between bg-gray-900 border border-gray-800 rounded-lg p-3">
            <div>
              <p className="text-sm font-medium">Flexible on dates?</p>
              <p className="text-[10px] text-gray-500">We'll suggest alternatives if denied</p>
            </div>
            <div className="w-10 h-5 bg-gray-700 rounded-full relative cursor-pointer">
              <div className="w-4 h-4 bg-gray-400 rounded-full absolute top-0.5 left-0.5"></div>
            </div>
          </div>

          {/* Coverage check preview */}
          <div className="bg-green-950 border border-green-800 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-1">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span className="text-xs text-green-400 font-medium">Coverage Check: PASS</span>
            </div>
            <p className="text-xs text-gray-400">
              Min staffing maintained. 3 spots available on your shift code.
              Advance notice requirement (14 days) met.
            </p>
            <p className="text-xs text-green-400 mt-1 font-medium">
              Likely auto-approved (no manager review needed)
            </p>
          </div>

          {/* Balance impact */}
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-3 space-y-2">
            <p className="text-xs text-gray-500 font-medium uppercase">Balance Impact</p>
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-400">Current PTO:</span>
              <span className="font-medium">48h (6 days)</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-400">This request:</span>
              <span className="text-red-400 font-medium">-40h (5 days)</span>
            </div>
            <div className="flex items-center justify-between text-sm border-t border-gray-800 pt-2">
              <span className="text-gray-400">Remaining after:</span>
              <span className="text-yellow-400 font-medium">8h (1 day)</span>
            </div>
          </div>

          {/* Submit */}
          <button
            onClick={() => setSubmitted(true)}
            className="w-full bg-brand-600 hover:bg-brand-700 py-3 rounded-lg font-medium transition"
          >
            Submit Request
          </button>
        </div>
      )}

      {/* Success state */}
      {activeTab === 'new' && submitted && (
        <div className="space-y-4 py-6">
          <div className="text-center">
            <div className="w-16 h-16 bg-green-900 rounded-full flex items-center justify-center mx-auto">
              <svg className="w-8 h-8 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="text-xl font-bold mt-3">Request Auto-Approved!</h2>
            <p className="text-gray-400 text-sm mt-1">
              Your PTO for Aug 10-14 has been approved automatically.
              Coverage is maintained and all compliance checks passed.
            </p>
          </div>

          {/* Live balance update */}
          <div className="bg-green-950 border border-green-800 rounded-xl p-4">
            <p className="text-xs text-green-400 font-medium uppercase mb-2">Balance Updated</p>
            <div className="grid grid-cols-3 gap-3 text-center">
              <div>
                <p className="text-lg font-bold text-red-400">-40h</p>
                <p className="text-[10px] text-gray-500">Deducted</p>
              </div>
              <div>
                <p className="text-lg font-bold text-white">8h</p>
                <p className="text-[10px] text-gray-500">PTO Remaining</p>
              </div>
              <div>
                <p className="text-lg font-bold text-green-400">1 day</p>
                <p className="text-[10px] text-gray-500">PTO Left</p>
              </div>
            </div>
          </div>

          {/* Confirmation details */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 text-sm space-y-2">
            <p className="text-xs text-gray-500 font-medium uppercase">Request Details</p>
            <div className="flex justify-between"><span className="text-gray-400">Request ID</span><span>REQ-005</span></div>
            <div className="flex justify-between"><span className="text-gray-400">Status</span><span className="text-green-400 font-medium">Auto-Approved</span></div>
            <div className="flex justify-between"><span className="text-gray-400">Dates</span><span>Aug 10-14 (5 days)</span></div>
            <div className="flex justify-between"><span className="text-gray-400">PTO deducted</span><span>40h</span></div>
          </div>

          {/* Notifications sent */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 space-y-3">
            <p className="text-xs text-gray-500 font-medium uppercase">Notifications Sent</p>
            <div className="flex items-start gap-2">
              <span className="text-green-400">✅</span>
              <div>
                <p className="text-sm font-medium">You</p>
                <p className="text-xs text-gray-400">"Your PTO for Aug 10-14 is confirmed. Coverage maintained. Enjoy your time off!"</p>
              </div>
            </div>
            <div className="flex items-start gap-2">
              <span className="text-blue-400">📋</span>
              <div>
                <p className="text-sm font-medium">Your Manager</p>
                <p className="text-xs text-gray-400">"Sarah Chen PTO auto-approved (Aug 10-14). Coverage OK — no action needed."</p>
              </div>
            </div>
          </div>

          <button
            onClick={() => setSubmitted(false)}
            className="w-full border border-gray-700 hover:border-gray-500 py-2.5 rounded-lg text-sm text-gray-300 transition"
          >
            Submit Another Request
          </button>
        </div>
      )}

      {/* History tab */}
      {activeTab === 'history' && (
        <div className="space-y-3">
          {DEMO_HISTORY.map(req => (
            <div key={req.id} className="bg-gray-900 border border-gray-800 rounded-xl p-3.5">
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    req.type === 'pto' ? 'bg-cyan-900 text-cyan-400' :
                    req.type === 'sick' ? 'bg-orange-900 text-orange-400' :
                    'bg-gray-800 text-gray-400'
                  }`}>
                    {req.type.toUpperCase()}
                  </span>
                  <span className="text-sm font-medium">{req.dates}</span>
                </div>
                <span className={`text-xs font-medium ${
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
              <p className="text-[10px] text-gray-600 mt-1">{req.id}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
