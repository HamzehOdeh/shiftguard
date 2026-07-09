'use client'

import Link from 'next/link'

const RESIDENTS = [
  { name: 'Dr. Patel', pgy: 'PGY-3', hours: 62, cap: 80, risk: 'SAFE', fatigue: 28 },
  { name: 'Dr. Kim', pgy: 'PGY-2', hours: 71, cap: 80, risk: 'MODERATE', fatigue: 55 },
  { name: 'Dr. Santos', pgy: 'PGY-1', hours: 45, cap: 80, risk: 'SAFE', fatigue: 18 },
  { name: 'Dr. Chen', pgy: 'PGY-3', hours: 74, cap: 80, risk: 'HIGH', fatigue: 68 },
  { name: 'Dr. Reeves', pgy: 'PGY-2', hours: 58, cap: 80, risk: 'SAFE', fatigue: 32 },
]

export default function HealthcareHomePage() {
  const totalViolations = 0
  const avgHours = Math.round(RESIDENTS.reduce((s, r) => s + r.hours, 0) / RESIDENTS.length)

  return (
    <div className="px-5 py-6 space-y-6">
      {/* Compliance Status Hero */}
      <div className="bg-green-500/10 border border-green-500/20 rounded-2xl p-5 shadow-elevation-1">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
          <span className="text-green-400 font-semibold text-body-sm">All {RESIDENTS.length} Residents ACGME-Compliant</span>
        </div>
        <p className="text-gray-300 text-body-sm">No duty hour violations. Next closest to cap: Dr. Chen (74h/80h).</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-gray-800/80 border border-gray-700 rounded-2xl p-4 shadow-elevation-1">
          <p className="text-xs text-gray-400 uppercase tracking-wide">Violations</p>
          <p className="text-heading-md font-bold text-green-400 mt-1">{totalViolations}</p>
          <p className="text-xs text-gray-400 mt-1">This week</p>
        </div>
        <div className="bg-gray-800/80 border border-gray-700 rounded-2xl p-4 shadow-elevation-1">
          <p className="text-xs text-gray-400 uppercase tracking-wide">Avg Hours</p>
          <p className="text-heading-md font-bold mt-1">{avgHours}h</p>
          <p className="text-xs text-gray-400 mt-1">/ 80h ACGME cap</p>
        </div>
        <div className="bg-gray-800/80 border border-gray-700 rounded-2xl p-4 shadow-elevation-1">
          <p className="text-xs text-gray-400 uppercase tracking-wide">Jeopardy</p>
          <p className="text-heading-md font-bold text-brand-400 mt-1">Ready</p>
          <p className="text-xs text-gray-400 mt-1">Backup assigned</p>
        </div>
        <div className="bg-gray-800/80 border border-gray-700 rounded-2xl p-4 shadow-elevation-1">
          <p className="text-xs text-gray-400 uppercase tracking-wide">Coverage</p>
          <p className="text-heading-md font-bold mt-1">100%</p>
          <p className="text-xs text-gray-400 mt-1">All shifts filled</p>
        </div>
      </div>

      {/* Resident Duty Hours */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-body-sm font-semibold">Resident Duty Hours</h3>
          <Link href="/healthcare/app/residency" className="text-xs text-brand-400">View All</Link>
        </div>
        <div className="space-y-2">
          {RESIDENTS.map(r => (
            <div key={r.name} className="bg-gray-800/80 border border-gray-700 rounded-xl px-4 py-3 shadow-elevation-1">
              <div className="flex items-center justify-between mb-2">
                <div>
                  <span className="text-body-sm font-medium">{r.name}</span>
                  <span className="text-xs text-gray-400 ml-2">{r.pgy}</span>
                </div>
                <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                  r.risk === 'SAFE' ? 'bg-green-500/15 text-green-400' :
                  r.risk === 'MODERATE' ? 'bg-yellow-500/15 text-yellow-400' :
                  'bg-red-500/15 text-red-400'
                }`}>{r.risk}</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="flex-1 h-2 bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${
                      r.risk === 'SAFE' ? 'bg-green-500' :
                      r.risk === 'MODERATE' ? 'bg-yellow-500' :
                      'bg-red-500'
                    }`}
                    style={{ width: `${(r.hours / r.cap) * 100}%` }}
                  />
                </div>
                <span className="text-xs text-gray-300 w-14 text-right">{r.hours}/{r.cap}h</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-2 gap-3">
        <Link href="/healthcare/app/otto" className="bg-gray-800/80 border border-gray-700 rounded-2xl p-4 text-center shadow-elevation-1 press-card">
          <span className="text-2xl block mb-1">🤖</span>
          <span className="text-body-sm font-medium">Ask Otto</span>
        </Link>
        <Link href="/healthcare/app/residency" className="bg-gray-800/80 border border-gray-700 rounded-2xl p-4 text-center shadow-elevation-1 press-card">
          <span className="text-2xl block mb-1">📊</span>
          <span className="text-body-sm font-medium">Full Dashboard</span>
        </Link>
      </div>
    </div>
  )
}
