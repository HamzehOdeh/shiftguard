'use client'

import { useState } from 'react'

const RESIDENTS = [
  { id: 'R001', name: 'Dr. Patel', pgy: 'PGY-3', weekHours: 62, fourWeekAvg: 65, consecutive: 4, nightsThisMonth: 5, fatigue: 28, risk: 'SAFE', rotation: 'Clinical - ED', nextShift: 'Tomorrow 07:00' },
  { id: 'R002', name: 'Dr. Kim', pgy: 'PGY-2', weekHours: 71, fourWeekAvg: 68, consecutive: 5, nightsThisMonth: 6, fatigue: 55, risk: 'MODERATE', rotation: 'Night Float', nextShift: 'Tonight 19:00' },
  { id: 'R003', name: 'Dr. Santos', pgy: 'PGY-1', weekHours: 45, fourWeekAvg: 52, consecutive: 3, nightsThisMonth: 3, fatigue: 18, risk: 'SAFE', rotation: 'Clinical - ED', nextShift: 'Tomorrow 07:00' },
  { id: 'R004', name: 'Dr. Chen', pgy: 'PGY-3', weekHours: 74, fourWeekAvg: 71, consecutive: 6, nightsThisMonth: 5, fatigue: 68, risk: 'HIGH', rotation: 'Clinical - Trauma', nextShift: 'Today 07:00' },
  { id: 'R005', name: 'Dr. Reeves', pgy: 'PGY-2', weekHours: 58, fourWeekAvg: 60, consecutive: 3, nightsThisMonth: 4, fatigue: 32, risk: 'SAFE', rotation: 'Elective', nextShift: 'Monday 07:00' },
]

const ACGME_RULES = [
  { rule: '80-Hour Weekly Limit', desc: 'Averaged over 4 weeks, inclusive of moonlighting', status: 'PASS' },
  { rule: '24+4 Continuous Duty', desc: 'Max 24h on-duty + 4h for transitions/education', status: 'PASS' },
  { rule: '8-Hour Rest Between', desc: 'Minimum 8h free between duty periods', status: 'PASS' },
  { rule: '14-Hour Daily Max', desc: 'After 24h duty, no new patients after 24h', status: 'PASS' },
  { rule: 'One Day Off in 7', desc: 'Averaged over 4 weeks', status: 'PASS' },
  { rule: 'Night Float Max 6', desc: 'No more than 6 consecutive nights', status: 'WARN' },
  { rule: 'Every 3rd Night Call', desc: 'No more frequent than every 3rd night', status: 'PASS' },
]

export default function ResidencyPage() {
  const [selectedResident, setSelectedResident] = useState<string | null>(null)
  const selected = RESIDENTS.find(r => r.id === selectedResident)

  return (
    <div className="px-5 py-6 space-y-6">
      <h2 className="text-heading-sm font-bold">Residency Program</h2>

      {/* ACGME Rules Status */}
      <div className="bg-gray-800/80 border border-gray-700 rounded-2xl p-4 shadow-elevation-1">
        <h3 className="text-body-sm font-semibold mb-3">ACGME Compliance Rules</h3>
        <div className="space-y-2">
          {ACGME_RULES.map(r => (
            <div key={r.rule} className="flex items-center justify-between">
              <div className="flex-1 min-w-0">
                <p className="text-body-sm font-medium truncate">{r.rule}</p>
                <p className="text-xs text-gray-400 truncate">{r.desc}</p>
              </div>
              <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ml-2 ${
                r.status === 'PASS' ? 'bg-green-500/15 text-green-400' : 'bg-yellow-500/15 text-yellow-400'
              }`}>{r.status}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Resident Cards */}
      <div>
        <h3 className="text-body-sm font-semibold mb-3">All Residents</h3>
        <div className="space-y-3">
          {RESIDENTS.map(r => (
            <button
              key={r.id}
              onClick={() => setSelectedResident(selectedResident === r.id ? null : r.id)}
              className="w-full text-left bg-gray-800/80 border border-gray-700 rounded-2xl p-4 shadow-elevation-1 press-card"
            >
              <div className="flex items-center justify-between mb-2">
                <div>
                  <span className="text-body-sm font-semibold">{r.name}</span>
                  <span className="text-xs text-gray-400 ml-2">{r.pgy}</span>
                </div>
                <span className={`text-xs font-semibold px-2.5 py-0.5 rounded-full ${
                  r.risk === 'SAFE' ? 'bg-green-500/15 text-green-400' :
                  r.risk === 'MODERATE' ? 'bg-yellow-500/15 text-yellow-400' :
                  'bg-red-500/15 text-red-400'
                }`}>{r.risk}</span>
              </div>

              {/* Hours bar */}
              <div className="flex items-center gap-3 mb-2">
                <div className="flex-1 h-2.5 bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${
                      r.risk === 'SAFE' ? 'bg-green-500' :
                      r.risk === 'MODERATE' ? 'bg-yellow-500' :
                      'bg-red-500'
                    }`}
                    style={{ width: `${(r.weekHours / 80) * 100}%` }}
                  />
                </div>
                <span className="text-xs text-gray-300 font-medium w-16 text-right">{r.weekHours}/80h</span>
              </div>

              <div className="flex items-center gap-4 text-xs text-gray-400">
                <span>Fatigue: {r.fatigue}/100</span>
                <span>Consec: {r.consecutive}d</span>
                <span>Nights: {r.nightsThisMonth}</span>
              </div>

              {/* Expanded detail */}
              {selectedResident === r.id && (
                <div className="mt-3 pt-3 border-t border-gray-700 space-y-2">
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-400">4-week average</span>
                    <span className="text-gray-200 font-medium">{r.fourWeekAvg}h/week</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-400">Current rotation</span>
                    <span className="text-gray-200 font-medium">{r.rotation}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-400">Next shift</span>
                    <span className="text-gray-200 font-medium">{r.nextShift}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-400">ACGME remaining</span>
                    <span className="text-green-400 font-medium">{80 - r.weekHours}h this week</span>
                  </div>
                </div>
              )}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

