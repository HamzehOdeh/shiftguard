'use client'

import { useState } from 'react'

export default function ReportingPage() {
  const [timeRange, setTimeRange] = useState('30')
  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <header className="border-b border-gray-800 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-brand-500 rounded-lg flex items-center justify-center text-sm font-bold">SG</div>
          <div>
            <h1 className="text-lg font-bold">ShiftGuard Reporting</h1>
            <p className="text-xs text-gray-500">Analytics & ROI Dashboard</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <select value={timeRange} onChange={(e) => setTimeRange(e.target.value)} className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-white">
            <option value="30">Last 30 days</option>
            <option value="90">Last 90 days</option>
            <option value="ytd">Year to date</option>
            <option value="all">All time</option>
          </select>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        {/* ROI Hero */}
        <div className="bg-gradient-to-r from-green-950 to-gray-900 border border-green-800 rounded-2xl p-8 text-center">
          <p className="text-green-400 text-sm font-medium uppercase tracking-wide mb-2">Estimated Annual Savings</p>
          <h2 className="text-5xl font-bold text-green-400 mb-2">$127,400</h2>
          <p className="text-gray-400">Based on current violation rates and operational metrics</p>
          <div className="grid grid-cols-3 gap-6 mt-6 max-w-2xl mx-auto">
            <div>
              <p className="text-2xl font-bold text-red-400">$91,000</p>
              <p className="text-xs text-gray-500">Penalties Avoided/yr</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-blue-400">$22,900</p>
              <p className="text-xs text-gray-500">Manager Time Saved/yr</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-purple-400">$13,500</p>
              <p className="text-xs text-gray-500">Retention Savings/yr</p>
            </div>
          </div>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <KPICard label="Compliance Score" value="87/100" trend="+12" trendUp />
          <KPICard label="Auto-Resolution Rate" value="84%" trend="+6%" trendUp />
          <KPICard label="Avg Gap Fill Time" value="12 min" trend="-48 min" trendUp />
          <KPICard label="Schedule Fairness" value="0.92" trend="+0.15" trendUp />
        </div>

        {/* Two-column layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Compliance Trend */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <h3 className="text-sm font-medium text-gray-400 uppercase mb-4">Violations Per Week (12-Week Trend)</h3>
            <div className="flex items-end gap-1 h-40">
              {[14, 12, 11, 13, 9, 8, 7, 6, 5, 4, 4, 3].map((v, i) => (
                <div key={i} className="flex-1 flex flex-col items-center justify-end h-full">
                  <div
                    className={`w-full rounded-t ${i >= 9 ? 'bg-green-600' : i >= 6 ? 'bg-yellow-600' : 'bg-red-600'}`}
                    style={{ height: `${(v / 14) * 100}%` }}
                  ></div>
                  <span className="text-[8px] text-gray-600 mt-1">{v}</span>
                </div>
              ))}
            </div>
            <div className="flex justify-between text-[10px] text-gray-600 mt-2">
              <span>12 weeks ago</span>
              <span>This week</span>
            </div>
            <p className="text-xs text-green-400 mt-3">78% reduction in violations since ShiftGuard activation</p>
          </div>

          {/* Penalty Exposure */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <h3 className="text-sm font-medium text-gray-400 uppercase mb-4">Weekly Penalty Exposure ($)</h3>
            <div className="flex items-end gap-1 h-40">
              {[8500, 7200, 6800, 8100, 5400, 4900, 4200, 3600, 3100, 2400, 2200, 1750].map((v, i) => (
                <div key={i} className="flex-1 flex flex-col items-center justify-end h-full">
                  <div
                    className="w-full bg-red-800 rounded-t"
                    style={{ height: `${(v / 8500) * 100}%` }}
                  ></div>
                  <span className="text-[7px] text-gray-600 mt-1">${(v/1000).toFixed(1)}k</span>
                </div>
              ))}
            </div>
            <div className="flex justify-between text-[10px] text-gray-600 mt-2">
              <span>12 weeks ago</span>
              <span>This week</span>
            </div>
            <p className="text-xs text-green-400 mt-3">$6,750/week saved vs baseline ($8,500 to $1,750)</p>
          </div>

          {/* Attendance Patterns */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <h3 className="text-sm font-medium text-gray-400 uppercase mb-4">Callout Patterns by Day</h3>
            <div className="space-y-2">
              {[
                { day: 'Monday', count: 7, pct: 100 },
                { day: 'Friday', count: 6, pct: 85 },
                { day: 'Saturday', count: 5, pct: 71 },
                { day: 'Sunday', count: 4, pct: 57 },
                { day: 'Thursday', count: 3, pct: 43 },
                { day: 'Wednesday', count: 2, pct: 28 },
                { day: 'Tuesday', count: 1, pct: 14 },
              ].map(d => (
                <div key={d.day} className="flex items-center gap-3">
                  <span className="text-xs text-gray-400 w-20">{d.day}</span>
                  <div className="flex-1 h-4 bg-gray-800 rounded-full overflow-hidden">
                    <div className="h-full bg-orange-600 rounded-full" style={{ width: `${d.pct}%` }}></div>
                  </div>
                  <span className="text-xs text-gray-400 w-6">{d.count}</span>
                </div>
              ))}
            </div>
            <p className="text-xs text-gray-500 mt-3">Monday/Friday callouts 3x higher than mid-week</p>
          </div>

          {/* Fairness Distribution */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <h3 className="text-sm font-medium text-gray-400 uppercase mb-4">Fairness Index by Employee</h3>
            <div className="space-y-2">
              {[
                { name: 'Sarah M.', idx: 4.2, bar: 84 },
                { name: 'James K.', idx: 3.8, bar: 76 },
                { name: 'Maria R.', idx: 3.5, bar: 70 },
                { name: 'Ahmed H.', idx: 3.3, bar: 66 },
                { name: 'Chen W.', idx: 3.1, bar: 62 },
                { name: 'Lisa P.', idx: 2.9, bar: 58 },
                { name: 'David T.', idx: 2.7, bar: 54 },
              ].map(emp => (
                <div key={emp.name} className="flex items-center gap-3">
                  <span className="text-xs text-gray-400 w-20 truncate">{emp.name}</span>
                  <div className="flex-1 h-4 bg-gray-800 rounded-full overflow-hidden">
                    <div className={`h-full rounded-full ${
                      emp.idx > 4 ? 'bg-red-600' : emp.idx > 3.5 ? 'bg-yellow-600' : 'bg-green-600'
                    }`} style={{ width: `${emp.bar}%` }}></div>
                  </div>
                  <span className="text-xs text-gray-400 w-8">{emp.idx}</span>
                </div>
              ))}
            </div>
            <p className="text-xs text-gray-500 mt-3">Lower = more equitable. Range: 2.7-4.2 (gap: 1.5 - acceptable)</p>
          </div>
        </div>

        {/* Before/After Comparison */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <h3 className="text-sm font-medium text-gray-400 uppercase mb-4">Before vs After ShiftGuard</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[
              { metric: 'Violations/week', before: '14', after: '3', improvement: '-79%', color: 'text-green-400' },
              { metric: 'Penalty exposure', before: '$8,500/wk', after: '$1,750/wk', improvement: '-79%', color: 'text-green-400' },
              { metric: 'Gap fill time', before: '2-4 hours', after: '12 minutes', improvement: '-95%', color: 'text-green-400' },
              { metric: 'Manager scheduling hours', before: '12h/week', after: '4h/week', improvement: '-67%', color: 'text-green-400' },
              { metric: 'Auto-resolution rate', before: '0%', after: '84%', improvement: 'New', color: 'text-blue-400' },
              { metric: 'Fairness tracking', before: 'None', after: 'Real-time', improvement: 'New', color: 'text-blue-400' },
            ].map(row => (
              <div key={row.metric} className="bg-gray-800 rounded-lg p-4">
                <p className="text-xs text-gray-500 mb-2">{row.metric}</p>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-gray-500">Before</p>
                    <p className="text-sm text-red-400 line-through">{row.before}</p>
                  </div>
                  <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                  </svg>
                  <div className="text-right">
                    <p className="text-xs text-gray-500">After</p>
                    <p className={`text-sm font-bold ${row.color}`}>{row.after}</p>
                  </div>
                </div>
                <p className={`text-xs ${row.color} text-center mt-2 font-medium`}>{row.improvement}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Investment Analysis */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <h3 className="text-sm font-medium text-gray-400 uppercase mb-4">Investment Analysis</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-white">$9,000</p>
              <p className="text-xs text-gray-500">Annual Cost (50 emp @ $15 PEPM)</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-green-400">$127,400</p>
              <p className="text-xs text-gray-500">Annual Savings</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-green-400">1,316%</p>
              <p className="text-xs text-gray-500">ROI</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-blue-400">0.8 mo</p>
              <p className="text-xs text-gray-500">Payback Period</p>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

function KPICard({ label, value, trend, trendUp }: {
  label: string; value: string; trend: string; trendUp: boolean
}) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className="text-2xl font-bold">{value}</p>
      <p className={`text-xs mt-1 ${trendUp ? 'text-green-400' : 'text-red-400'}`}>
        {trend} vs last month
      </p>
    </div>
  )
}
