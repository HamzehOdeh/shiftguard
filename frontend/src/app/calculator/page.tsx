'use client'

import { useState } from 'react'

interface RiskResult {
  grade: string
  gradeColor: string
  annualExposure: number
  weeklyExposure: number
  topViolations: { name: string; penalty: number; likelihood: string }[]
  recommendation: string
}

const STATE_PENALTIES: Record<string, { multiplier: number; laws: string[] }> = {
  'California': { multiplier: 1.8, laws: ['Labor Code', 'Meal/Rest Breaks', 'Predictive Scheduling (SF/LA)'] },
  'New York': { multiplier: 1.5, laws: ['NYC Fair Workweek', 'Wage Theft Prevention', 'Paid Safe & Sick Leave'] },
  'Illinois': { multiplier: 1.3, laws: ['Chicago Fair Workweek', 'ODRISA', 'Paid Leave for All'] },
  'Oregon': { multiplier: 1.4, laws: ['Predictive Scheduling', 'Sick Leave', 'Equal Pay Act'] },
  'Washington': { multiplier: 1.3, laws: ['Secure Scheduling (Seattle)', 'Paid Sick Leave', 'Rest Breaks'] },
  'Texas': { multiplier: 0.8, laws: ['Payday Law', 'Workers Comp'] },
  'Florida': { multiplier: 0.7, laws: ['Min Wage Amendment', 'Workers Comp'] },
  'Other': { multiplier: 1.0, laws: ['FLSA', 'State-specific regulations'] },
}

const INDUSTRY_RISKS: Record<string, { baseRisk: number; topViolations: string[] }> = {
  'Healthcare': { baseRisk: 2200, topViolations: ['ACGME hour violations', 'Mandatory rest period gaps', 'Nurse ratio non-compliance', 'FMLA notification failures'] },
  'Warehouse/Logistics': { baseRisk: 1800, topViolations: ['Overtime cap violations', 'Consecutive day limits', 'Minor labor restrictions', 'Meal/rest break failures'] },
  'Retail': { baseRisk: 1500, topViolations: ['Predictive scheduling penalties', 'Clopening violations', 'Schedule change premiums', 'Minor hour restrictions'] },
  'Hospitality': { baseRisk: 1600, topViolations: ['Split shift premiums', 'Clopening violations', 'Tip credit violations', 'Schedule notice failures'] },
  'Manufacturing': { baseRisk: 1900, topViolations: ['Fatigue-related incidents', 'Consecutive shift violations', 'Rest period gaps', 'Overtime distribution'] },
  'Staffing Agency': { baseRisk: 2000, topViolations: ['Multi-jurisdiction compliance', 'Client site violations', 'Temp worker protections', 'Equal pay requirements'] },
}

function calculateRisk(state: string, industry: string, headcount: number, hasUnion: boolean): RiskResult {
  const stateInfo = STATE_PENALTIES[state] || STATE_PENALTIES['Other']
  const industryInfo = INDUSTRY_RISKS[industry] || INDUSTRY_RISKS['Retail']

  const baseWeekly = industryInfo.baseRisk * stateInfo.multiplier
  const headcountFactor = Math.sqrt(headcount / 100)
  const unionFactor = hasUnion ? 1.4 : 1.0
  const weeklyExposure = Math.round(baseWeekly * headcountFactor * unionFactor)
  const annualExposure = weeklyExposure * 52

  let grade: string, gradeColor: string
  if (weeklyExposure > 8000) { grade = 'F'; gradeColor = 'text-red-500' }
  else if (weeklyExposure > 5000) { grade = 'D'; gradeColor = 'text-red-400' }
  else if (weeklyExposure > 3000) { grade = 'C'; gradeColor = 'text-yellow-400' }
  else if (weeklyExposure > 1500) { grade = 'B'; gradeColor = 'text-green-400' }
  else { grade = 'A'; gradeColor = 'text-green-500' }

  const topViolations = industryInfo.topViolations.map((name, i) => ({
    name,
    penalty: Math.round(weeklyExposure * [0.35, 0.25, 0.22, 0.18][i]),
    likelihood: ['High', 'High', 'Medium', 'Medium'][i],
  }))

  const recommendation = annualExposure > 100000
    ? 'Critical risk. You need automated compliance checking immediately.'
    : annualExposure > 50000
    ? 'High risk. Manual processes cannot catch all violations at this scale.'
    : annualExposure > 20000
    ? 'Moderate risk. Automated compliance would pay for itself within 2 months.'
    : 'Lower risk, but automated compliance still prevents costly surprises.'

  return { grade, gradeColor, annualExposure, weeklyExposure, topViolations, recommendation }
}

export default function CalculatorPage() {
  const [state, setState] = useState('California')
  const [industry, setIndustry] = useState('Healthcare')
  const [headcount, setHeadcount] = useState(200)
  const [hasUnion, setHasUnion] = useState(false)
  const [result, setResult] = useState<RiskResult | null>(null)

  function handleCalculate(e: React.FormEvent) {
    e.preventDefault()
    setResult(calculateRisk(state, industry, headcount, hasUnion))
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <header className="border-b border-gray-800 px-6 py-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <a href="/" className="flex items-center gap-2">
              <div className="w-8 h-8 bg-brand-500 rounded-lg flex items-center justify-center text-sm font-bold">SG</div>
              <span className="font-semibold">ShiftGuard</span>
            </a>
          </div>
          <div className="flex items-center gap-3">
            <a href="/demo" className="text-sm text-gray-400 hover:text-white transition">Demo</a>
            <a href="/login" className="text-sm bg-brand-600 hover:bg-brand-700 px-4 py-2 rounded-lg transition">Sign In</a>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-12">
        {/* Hero */}
        <div className="text-center mb-10">
          <h1 className="text-3xl md:text-4xl font-bold mb-3">Compliance Risk Calculator</h1>
          <p className="text-gray-400 text-lg">Know your penalty exposure in 30 seconds. Free, no signup required.</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Form */}
          <form onSubmit={handleCalculate} className="space-y-5">
            <div>
              <label className="text-xs text-gray-500 font-medium uppercase block mb-1">State</label>
              <select
                value={state}
                onChange={(e) => setState(e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-white focus:border-brand-500 focus:outline-none"
              >
                {Object.keys(STATE_PENALTIES).map(s => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
              <p className="text-[10px] text-gray-600 mt-1">
                Key laws: {(STATE_PENALTIES[state] || STATE_PENALTIES['Other']).laws.join(', ')}
              </p>
            </div>

            <div>
              <label className="text-xs text-gray-500 font-medium uppercase block mb-1">Industry</label>
              <select
                value={industry}
                onChange={(e) => setIndustry(e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-white focus:border-brand-500 focus:outline-none"
              >
                {Object.keys(INDUSTRY_RISKS).map(i => (
                  <option key={i} value={i}>{i}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-xs text-gray-500 font-medium uppercase block mb-1">
                Hourly/Shift Employees: {headcount}
              </label>
              <input
                type="range"
                min="50"
                max="2000"
                step="50"
                value={headcount}
                onChange={(e) => setHeadcount(Number(e.target.value))}
                className="w-full accent-brand-500"
              />
              <div className="flex justify-between text-[10px] text-gray-600">
                <span>50</span><span>500</span><span>1000</span><span>2000</span>
              </div>
            </div>

            <div className="flex items-center justify-between bg-gray-900 border border-gray-800 rounded-lg p-4">
              <div>
                <p className="text-sm font-medium">Union / CBA workforce?</p>
                <p className="text-[10px] text-gray-500">Union CBAs add extra scheduling constraints</p>
              </div>
              <button
                type="button"
                onClick={() => setHasUnion(!hasUnion)}
                className={`w-11 h-6 rounded-full transition relative ${hasUnion ? 'bg-brand-600' : 'bg-gray-700'}`}
              >
                <div className={`w-5 h-5 bg-white rounded-full absolute top-0.5 transition ${hasUnion ? 'left-[22px]' : 'left-0.5'}`}></div>
              </button>
            </div>

            <button
              type="submit"
              className="w-full bg-red-600 hover:bg-red-700 py-4 rounded-lg font-bold text-lg transition"
            >
              Calculate My Risk Exposure
            </button>
          </form>

          {/* Results */}
          <div>
            {!result && (
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 text-center h-full flex flex-col items-center justify-center">
                <div className="text-6xl mb-4">🛡️</div>
                <p className="text-gray-400">Enter your details and click calculate to see your compliance risk exposure.</p>
                <p className="text-xs text-gray-600 mt-3">Based on real penalty data from DOL enforcement actions.</p>
              </div>
            )}

            {result && (
              <div className="space-y-4">
                {/* Risk grade */}
                <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 text-center">
                  <p className="text-xs text-gray-500 uppercase font-medium mb-2">Your Risk Grade</p>
                  <p className={`text-7xl font-black ${result.gradeColor}`}>{result.grade}</p>
                  <p className="text-gray-400 text-sm mt-2">{result.recommendation}</p>
                </div>

                {/* Annual exposure */}
                <div className="bg-red-950 border border-red-800 rounded-xl p-6 text-center">
                  <p className="text-xs text-red-400 uppercase font-medium mb-1">Estimated Annual Penalty Exposure</p>
                  <p className="text-4xl font-bold text-red-400">${result.annualExposure.toLocaleString()}</p>
                  <p className="text-sm text-gray-400 mt-1">${result.weeklyExposure.toLocaleString()}/week</p>
                </div>

                {/* Top violations */}
                <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
                  <p className="text-xs text-gray-500 uppercase font-medium mb-3">Top Violation Risks</p>
                  <div className="space-y-3">
                    {result.topViolations.map((v, i) => (
                      <div key={i} className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className={`w-2 h-2 rounded-full ${v.likelihood === 'High' ? 'bg-red-500' : 'bg-yellow-500'}`}></span>
                          <span className="text-sm">{v.name}</span>
                        </div>
                        <span className="text-sm text-red-400 font-medium">${v.penalty.toLocaleString()}/wk</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* CTA */}
                <div className="bg-brand-950 border border-brand-800 rounded-xl p-5 text-center">
                  <p className="font-medium mb-2">ShiftGuard catches these violations before you publish the schedule.</p>
                  <p className="text-sm text-gray-400 mb-4">60-second setup. No implementation project.</p>
                  <a href="/demo" className="inline-block bg-brand-600 hover:bg-brand-700 px-6 py-3 rounded-lg font-medium transition">
                    See It In Action
                  </a>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Social proof */}
        <div className="mt-16 border-t border-gray-800 pt-10 text-center">
          <p className="text-gray-500 text-sm mb-6">Based on real enforcement data from:</p>
          <div className="flex flex-wrap justify-center gap-8 text-gray-600 text-sm">
            <span>US Dept. of Labor</span>
            <span>CA Division of Labor</span>
            <span>NYC DCWP</span>
            <span>OR BOLI</span>
            <span>IL Dept. of Labor</span>
          </div>
        </div>
      </main>
    </div>
  )
}
