'use client'

const VIOLATIONS = [
  { severity: 'HIGH', employee: 'Dr. Chen', desc: 'Approaching 80h weekly cap (74h current)', penalty: '$2,500', fix: 'Remove Friday night shift or swap with Dr. Santos' },
  { severity: 'MEDIUM', employee: 'Dr. Kim', desc: '6 consecutive night shifts (max 6 per ACGME)', penalty: '$1,500', fix: 'Assign next night to Dr. Reeves or Dr. Patel' },
]

const AUDIT_LOG = [
  { time: '2h ago', action: 'VIOLATION_FIXED', actor: 'System (Auto)', target: 'Dr. Patel', detail: '80h limit approaching â€” removed Friday night shift' },
  { time: '3h ago', action: 'SWAP_APPROVED', actor: 'Dr. Kim', target: 'Dr. Santos', detail: 'Night swap â€” both ACGME-safe after swap' },
  { time: '4h ago', action: 'PTO_APPROVED', actor: 'System', target: 'RN Sarah Chen', detail: 'Auto-approved â€” coverage maintained' },
  { time: '6h ago', action: 'SCHEDULE_PUBLISHED', actor: 'Dr. Torres (PD)', target: 'Week Schedule', detail: 'All ACGME rules passed. Confidence: 98%' },
]

export default function AdminPage() {
  return (
    <div className="px-5 py-6 space-y-6">
      <h2 className="text-heading-sm font-bold">Admin & Compliance</h2>

      {/* Penalty exposure */}
      <div className="bg-gray-800/80 border border-gray-700 border-t-2 border-t-red-500 rounded-2xl p-5 shadow-elevation-2">
        <div className="flex items-center justify-between mb-2">
          <span className="text-body-sm font-semibold">Penalty Exposure</span>
          <span className="text-xs text-gray-400">Illinois (1.3x multiplier)</span>
        </div>
        <p className="text-heading-md font-bold text-red-400">$5,200/week</p>
        <p className="text-xs text-gray-300 mt-1">2 active violations. Fix now to reduce to $0.</p>
      </div>

      {/* Active violations */}
      <div>
        <h3 className="text-body-sm font-semibold mb-3">Active Violations</h3>
        <div className="space-y-3">
          {VIOLATIONS.map((v, i) => (
            <div key={i} className={`bg-gray-800/80 border rounded-2xl p-4 shadow-elevation-1 ${
              v.severity === 'HIGH' ? 'border-red-500/30' : 'border-yellow-500/30'
            }`}>
              <div className="flex items-center gap-2 mb-2">
                <span className={`text-xs font-bold px-2 py-0.5 rounded ${
                  v.severity === 'HIGH' ? 'bg-red-500/20 text-red-400' : 'bg-yellow-500/20 text-yellow-400'
                }`}>{v.severity}</span>
                <span className="text-body-sm font-medium">{v.employee}</span>
                <span className="text-xs text-gray-400 ml-auto">{v.penalty}</span>
              </div>
              <p className="text-body-sm text-gray-300">{v.desc}</p>
              <p className="text-xs text-green-400 mt-2">Fix: {v.fix}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Audit trail */}
      <div>
        <h3 className="text-body-sm font-semibold mb-3">Activity Log</h3>
        <div className="space-y-2">
          {AUDIT_LOG.map((log, i) => (
            <div key={i} className="bg-gray-800/80 border border-gray-700 rounded-xl px-4 py-3 shadow-elevation-1">
              <div className="flex items-center justify-between mb-1">
                <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                  log.action.includes('FIXED') ? 'bg-green-500/15 text-green-400' :
                  log.action.includes('APPROVED') ? 'bg-cyan-500/15 text-cyan-400' :
                  log.action.includes('PUBLISHED') ? 'bg-brand-500/15 text-brand-400' :
                  'bg-gray-700 text-gray-400'
                }`}>{log.action}</span>
                <span className="text-xs text-gray-400">{log.time}</span>
              </div>
              <p className="text-xs text-gray-300">{log.actor} â†’ {log.target}</p>
              <p className="text-xs text-gray-400 mt-0.5">{log.detail}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

