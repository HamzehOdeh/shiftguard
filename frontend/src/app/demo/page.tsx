'use client'

import { useState, useEffect, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'

type Industry = 'healthcare' | 'warehouse' | 'retail' | 'hospitality' | 'manufacturing'

interface Violation {
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM'
  rule: string
  employee: string
  description: string
  fix: string
  penalty: number
}

const DEMO_DATA: Record<Industry, { facility: string; violations: Violation[]; employees: number; shifts: number }> = {
  healthcare: {
    facility: 'Metro General Hospital — Emergency Department',
    employees: 12,
    shifts: 84,
    violations: [
      { severity: 'CRITICAL', rule: 'ACGME-001', employee: 'Dr. Patel', description: 'Resident exceeded 80hr/week limit (84h scheduled)', fix: 'Remove Friday night shift, redistribute to Dr. Kim', penalty: 7500 },
      { severity: 'CRITICAL', rule: 'REST-002', employee: 'RN Sarah Chen', description: 'Less than 8h rest between shifts (clopening: 11PM close, 6AM open)', fix: 'Move morning shift to start at 10AM or swap with RN Martinez', penalty: 5000 },
      { severity: 'HIGH', rule: 'CONSEC-001', employee: 'RN James Wilson', description: '7 consecutive days worked (max 6 per CBA)', fix: 'Cancel Sunday shift, offer VET to available staff', penalty: 2000 },
      { severity: 'HIGH', rule: 'OT-003', employee: 'Tech Ahmed Hassan', description: 'Scheduled for 52h (12h overtime without prior approval)', fix: 'Reduce Thursday shift or redistribute to part-time staff', penalty: 1500 },
      { severity: 'MEDIUM', rule: 'NOTICE-001', employee: 'All ED Staff', description: 'Schedule posted 5 days before start (minimum 14 days required by CBA)', fix: 'Publish schedules by Wednesday of prior week', penalty: 500 },
    ],
  },
  warehouse: {
    facility: 'ACME Fulfillment Center — PDX1',
    employees: 45,
    shifts: 315,
    violations: [
      { severity: 'CRITICAL', rule: 'OR-PRED-001', employee: 'Pick Team B', description: 'Schedule change within 14 days without premium pay (Oregon Predictive Scheduling)', fix: 'Pay $50/shift premium or revert to original schedule', penalty: 6000 },
      { severity: 'HIGH', rule: 'MINOR-001', employee: 'Alex Rodriguez (17)', description: 'Minor scheduled past 10PM (state limit for 16-17yr olds)', fix: 'End shift at 9:30PM maximum, reassign closing tasks', penalty: 3000 },
      { severity: 'HIGH', rule: 'CONSEC-002', employee: 'Maria Santos', description: '8 consecutive days without day off (CBA max: 6)', fix: 'Mandatory day off Tuesday, backfill with VET offer', penalty: 2500 },
      { severity: 'MEDIUM', rule: 'MEAL-001', employee: 'Stow Team A (4 workers)', description: 'No meal break scheduled in 10.5h shift (required at 5h mark)', fix: 'Add 30-min unpaid meal break at hour 5', penalty: 1000 },
      { severity: 'MEDIUM', rule: 'OT-DIST-001', employee: 'Jake Thompson', description: 'OT hours 3x team average (fairness violation per CBA Art. 12)', fix: 'Redistribute MET to lower-OT associates', penalty: 800 },
    ],
  },
  retail: {
    facility: 'Coastal Retail — Union Square Location',
    employees: 28,
    shifts: 196,
    violations: [
      { severity: 'CRITICAL', rule: 'SF-PRED-001', employee: 'All Associates', description: 'Schedule posted 10 days before (SF requires 14 days, penalty: $100-$500/worker/day)', fix: 'Publish by this Friday for next period', penalty: 8000 },
      { severity: 'HIGH', rule: 'CLOPEN-001', employee: 'Mia Johnson', description: 'Closing at 11PM Saturday, opening at 7AM Sunday (SF clopening ban, <11h gap)', fix: 'Offer $100 premium or swap Sunday opener with Tues staff', penalty: 3000 },
      { severity: 'HIGH', rule: 'AVAIL-001', employee: 'Part-Time Staff (6)', description: 'Shifts outside declared availability window without consent', fix: 'Check availability forms before publishing', penalty: 2000 },
      { severity: 'MEDIUM', rule: 'SPLIT-001', employee: 'Carlos Rivera', description: 'Split shift without premium (CA requires extra hour of pay)', fix: 'Add 1hr premium pay or consolidate into single block', penalty: 400 },
    ],
  },
  hospitality: {
    facility: 'Summit Grand Hotel — Downtown',
    employees: 35,
    shifts: 245,
    violations: [
      { severity: 'CRITICAL', rule: 'NYC-FWW-001', employee: 'Front Desk Team', description: 'On-call scheduling without pay (NYC Fast Food/Hotel Fair Workweek)', fix: 'Convert on-call to scheduled shifts or pay premium', penalty: 5500 },
      { severity: 'HIGH', rule: 'CLOPEN-002', employee: 'Lisa Park', description: 'Bar close at 2AM, front desk at 6AM (only 4h rest — NYC requires 11h)', fix: 'Move to afternoon shift or find swap partner', penalty: 3500 },
      { severity: 'HIGH', rule: 'SPREAD-001', employee: 'Banquet Staff (8)', description: 'Spread of hours exceeds 10h without extra pay (NY Labor Law)', fix: 'Add 1hr extra pay for each affected shift', penalty: 2000 },
      { severity: 'MEDIUM', rule: 'NOTICE-002', employee: 'Housekeeping', description: 'Shift cancellation within 48h (must pay 4h minimum)', fix: 'Pay show-up minimum or reassign to other duties', penalty: 1200 },
    ],
  },
  manufacturing: {
    facility: 'Precision Components — Plant #3',
    employees: 60,
    shifts: 420,
    violations: [
      { severity: 'CRITICAL', rule: 'FATIGUE-001', employee: 'Night Shift C', description: '3 workers on 7th consecutive 12h night shift (extreme fatigue risk, OSHA liability)', fix: 'Mandatory 48h rest period, activate relief crew', penalty: 9000 },
      { severity: 'HIGH', rule: 'OT-CAP-001', employee: 'CNC Team (5)', description: 'Scheduled for 60+ hours (state cap: 56h without written consent)', fix: 'Get written consent forms or reduce to 56h max', penalty: 4000 },
      { severity: 'HIGH', rule: 'ROTATION-001', employee: 'Line 4 Crew', description: 'Backward shift rotation (night→evening→day) increases accident risk 40%', fix: 'Switch to forward rotation (day→evening→night)', penalty: 2500 },
      { severity: 'MEDIUM', rule: 'REST-003', employee: 'Maintenance Crew', description: 'Only 6h between end of overtime and next shift start', fix: 'Push next shift start by 2h minimum', penalty: 1500 },
      { severity: 'MEDIUM', rule: 'CERT-001', employee: 'Tom Baker', description: 'Forklift certification expired 3 days ago — still scheduled for loading', fix: 'Remove from forklift duties until renewed', penalty: 1000 },
    ],
  },
}

export default function DemoPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-gray-950" />}>
      <DemoContent />
    </Suspense>
  )
}

function DemoContent() {
  const searchParams = useSearchParams()
  const initialIndustry = (searchParams.get('industry') as Industry) || 'healthcare'
  const [industry, setIndustry] = useState<Industry>(initialIndustry)
  const [showResults, setShowResults] = useState(true)

  useEffect(() => {
    const param = searchParams.get('industry') as Industry
    if (param && DEMO_DATA[param]) setIndustry(param)
  }, [searchParams])

  const data = DEMO_DATA[industry]
  const totalPenalty = data.violations.reduce((sum, v) => sum + v.penalty, 0)
  const criticalCount = data.violations.filter(v => v.severity === 'CRITICAL').length
  const highCount = data.violations.filter(v => v.severity === 'HIGH').length

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <header className="border-b border-gray-800 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <a href="/" className="flex items-center gap-2">
              <div className="w-8 h-8 bg-brand-500 rounded-lg flex items-center justify-center text-sm font-bold">SG</div>
              <span className="font-semibold">ShiftGuard</span>
            </a>
            <span className="text-xs bg-brand-900 text-brand-400 px-2 py-0.5 rounded-full">LIVE DEMO</span>
          </div>
          <div className="flex items-center gap-3">
            <a href="/calculator" className="text-sm text-gray-400 hover:text-white transition">Calculator</a>
            <a href="/login" className="text-sm bg-brand-600 hover:bg-brand-700 px-4 py-2 rounded-lg transition">Sign In</a>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8 space-y-6">
        {/* Industry selector */}
        <div className="flex flex-wrap gap-2">
          {(['healthcare', 'warehouse', 'retail', 'hospitality', 'manufacturing'] as Industry[]).map(ind => (
            <button
              key={ind}
              onClick={() => { setIndustry(ind); setShowResults(true) }}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                industry === ind
                  ? 'bg-brand-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
              }`}
            >
              {ind.charAt(0).toUpperCase() + ind.slice(1)}
            </button>
          ))}
        </div>

        {/* Facility info */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 flex items-center justify-between">
          <div>
            <p className="font-medium">{data.facility}</p>
            <p className="text-sm text-gray-400">{data.employees} employees | {data.shifts} shifts this week | Demo data</p>
          </div>
          <span className="text-xs bg-green-900 text-green-400 px-3 py-1 rounded-full">Analysis Complete</span>
        </div>

        {/* Penalty hero */}
        <div className="bg-gradient-to-r from-red-950 to-gray-900 border border-red-800 rounded-2xl p-8 text-center">
          <p className="text-red-400 text-sm font-medium uppercase tracking-wide mb-2">Weekly Penalty Exposure</p>
          <h2 className="text-5xl font-bold text-red-400 mb-2">${totalPenalty.toLocaleString()}</h2>
          <p className="text-gray-400">{data.violations.length} violations found | {criticalCount} critical, {highCount} high severity</p>
        </div>

        {/* Violations list */}
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-gray-400 uppercase">Violations Found</h3>
          {data.violations.map((v, i) => (
            <div key={i} className={`bg-gray-900 border rounded-xl p-4 ${
              v.severity === 'CRITICAL' ? 'border-red-800' :
              v.severity === 'HIGH' ? 'border-orange-800' :
              'border-gray-800'
            }`}>
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className={`text-xs px-2 py-0.5 rounded font-bold ${
                    v.severity === 'CRITICAL' ? 'bg-red-900 text-red-400' :
                    v.severity === 'HIGH' ? 'bg-orange-900 text-orange-400' :
                    'bg-yellow-900 text-yellow-400'
                  }`}>{v.severity}</span>
                  <span className="text-xs text-gray-500">{v.rule}</span>
                </div>
                <span className="text-sm text-red-400 font-bold">${v.penalty.toLocaleString()}/wk</span>
              </div>
              <p className="text-sm font-medium mb-1">{v.employee}</p>
              <p className="text-sm text-gray-400 mb-2">{v.description}</p>
              <p className="text-sm text-green-400">Fix: {v.fix}</p>
            </div>
          ))}
        </div>

        {/* CTA */}
        <div className="bg-brand-950 border border-brand-800 rounded-2xl p-8 text-center">
          <h3 className="text-xl font-bold mb-2">This runs automatically on every schedule you publish.</h3>
          <p className="text-gray-400 mb-6">Upload your real schedule CSV and see your actual violations in 60 seconds.</p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <a href="/login" className="bg-brand-600 hover:bg-brand-700 px-8 py-3 rounded-lg font-medium transition">
              Start Free Trial
            </a>
            <a href="/calculator" className="border border-gray-700 hover:border-gray-500 px-8 py-3 rounded-lg font-medium transition text-gray-300">
              Calculate My Risk First
            </a>
          </div>
        </div>
      </main>
    </div>
  )
}
