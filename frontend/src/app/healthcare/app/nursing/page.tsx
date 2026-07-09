'use client'

import { useState } from 'react'

const NURSES = [
  { name: 'Sarah Chen', role: 'Staff RN', unit: 'ED', shift: '07:00-19:00', hours: 36, fatigue: 22, status: 'On Shift' },
  { name: 'Maria Rodriguez', role: 'Staff RN', unit: 'ED', shift: 'Off Today', hours: 24, fatigue: 15, status: 'Off' },
  { name: 'James Wilson', role: 'Charge RN', unit: 'ED', shift: '07:00-19:00', hours: 38, fatigue: 35, status: 'On Shift' },
  { name: 'Aisha Johnson', role: 'Staff RN', unit: 'ICU', shift: '19:00-07:00', hours: 32, fatigue: 42, status: 'Night' },
  { name: 'Lisa Park', role: 'Travel RN', unit: 'ED', shift: '19:00-07:00', hours: 28, fatigue: 20, status: 'Night' },
  { name: 'Kim Park', role: 'Staff RN', unit: 'ED', shift: '07:00-19:00', hours: 36, fatigue: 30, status: 'On Shift' },
]

const CREDENTIALS = [
  { name: 'Sarah Chen', cred: 'BLS', expires: 'Dec 2026', status: 'Current' },
  { name: 'Sarah Chen', cred: 'ACLS', expires: 'Mar 2027', status: 'Current' },
  { name: 'Aisha Johnson', cred: 'NRP', expires: 'Aug 2026', status: 'Expiring Soon' },
  { name: 'Lisa Park', cred: 'ACLS', expires: 'Pending', status: 'Pending' },
]

export default function NursingPage() {
  const [tab, setTab] = useState<'team' | 'creds'>('team')
  const onShift = NURSES.filter(n => n.status === 'On Shift' || n.status === 'Night')

  return (
    <div className="px-5 py-6 space-y-6">
      <h2 className="text-heading-sm font-bold">Nursing Dashboard</h2>

      {/* Quick stats */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-surface-raised border border-white/[0.06] rounded-2xl p-3.5 text-center shadow-elevation-1">
          <p className="text-heading-sm font-bold text-green-400">{onShift.length}</p>
          <p className="text-xs text-gray-400">On Shift</p>
        </div>
        <div className="bg-surface-raised border border-white/[0.06] rounded-2xl p-3.5 text-center shadow-elevation-1">
          <p className="text-heading-sm font-bold">1:4</p>
          <p className="text-xs text-gray-400">RN Ratio</p>
        </div>
        <div className="bg-surface-raised border border-white/[0.06] rounded-2xl p-3.5 text-center shadow-elevation-1">
          <p className="text-heading-sm font-bold text-yellow-400">1</p>
          <p className="text-xs text-gray-400">Cred Expiring</p>
        </div>
      </div>

      {/* Tab toggle */}
      <div className="flex bg-surface-raised border border-white/[0.06] rounded-2xl p-1.5">
        <button
          onClick={() => setTab('team')}
          className={`flex-1 py-2.5 rounded-xl text-body-sm font-medium transition ${
            tab === 'team' ? 'bg-brand-600 text-white' : 'text-gray-400'
          }`}
        >Team</button>
        <button
          onClick={() => setTab('creds')}
          className={`flex-1 py-2.5 rounded-xl text-body-sm font-medium transition ${
            tab === 'creds' ? 'bg-brand-600 text-white' : 'text-gray-400'
          }`}
        >Credentials</button>
      </div>

      {tab === 'team' && (
        <div className="space-y-2">
          {NURSES.map(n => (
            <div key={n.name} className="bg-surface-raised border border-white/[0.06] rounded-xl px-4 py-3 shadow-elevation-1">
              <div className="flex items-center justify-between mb-1">
                <div>
                  <span className="text-body-sm font-medium">{n.name}</span>
                  <span className="text-xs text-gray-400 ml-2">{n.role}</span>
                </div>
                <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                  n.status === 'On Shift' ? 'bg-green-500/15 text-green-400' :
                  n.status === 'Night' ? 'bg-purple-500/15 text-purple-400' :
                  'bg-surface-highlight text-gray-400'
                }`}>{n.status}</span>
              </div>
              <div className="flex items-center gap-4 text-xs text-gray-400">
                <span>{n.unit}</span>
                <span>{n.shift}</span>
                <span>{n.hours}h/wk</span>
                <span>Fatigue: {n.fatigue}/100</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === 'creds' && (
        <div className="space-y-2">
          {CREDENTIALS.map((c, i) => (
            <div key={i} className="bg-surface-raised border border-white/[0.06] rounded-xl px-4 py-3 shadow-elevation-1">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-body-sm font-medium">{c.name}</span>
                  <span className="text-xs text-gray-400 ml-2">— {c.cred}</span>
                </div>
                <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                  c.status === 'Current' ? 'bg-green-500/15 text-green-400' :
                  c.status === 'Expiring Soon' ? 'bg-yellow-500/15 text-yellow-400' :
                  'bg-orange-500/15 text-orange-400'
                }`}>{c.status}</span>
              </div>
              <p className="text-xs text-gray-400 mt-1">Expires: {c.expires}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
