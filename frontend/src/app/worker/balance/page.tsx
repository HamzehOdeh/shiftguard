'use client'

function getNextPayDate() {
  const now = new Date()
  const d = new Date(now.getFullYear(), now.getMonth(), 15)
  if (d <= now) d.setMonth(d.getMonth() + 1)
  return d.toLocaleDateString('en-US', {month: 'short', day: 'numeric'})
}

function getNextQuarterStart() {
  const now = new Date()
  const q = Math.floor(now.getMonth() / 3) + 1
  const next = new Date(now.getFullYear(), q * 3, 1)
  return next.toLocaleDateString('en-US', {month: 'short', day: 'numeric'})
}

function getDaysUntilYearEnd() {
  const now = new Date()
  const yearEnd = new Date(now.getFullYear(), 11, 31)
  return Math.ceil((yearEnd.getTime() - now.getTime()) / 86400000)
}

function daysAgo(n: number) {
  const d = new Date()
  d.setDate(d.getDate() - n)
  return d.toLocaleDateString('en-US', {month: 'short', day: 'numeric'})
}

export default function WorkerBalancePage() {
  return (
    <div className="px-5 py-6 space-y-6">
      <div id="donate-toast" className="hidden fixed top-16 left-1/2 -translate-x-1/2 z-50 bg-green-500/10 border border-green-500/20 text-green-400 px-5 py-3.5 rounded-2xl shadow-elevation-2 text-body-sm font-medium backdrop-blur-sm">
        Leave donation request submitted to HR for approval.
      </div>
      <h1 className="text-heading-md font-bold">My Leave Balances</h1>

      {/* Primary balances */}
      <div className="space-y-3">
        <BalanceCard
          label="Paid Time Off (PTO)"
          available={48}
          used={32}
          total={80}
          unit="hours"
          color="cyan"
          details={[
            { label: 'Standard PTO', value: '36h available' },
            { label: 'Flex PTO', value: '12h available' },
            { label: 'Accrual rate', value: '3.08h / pay period' },
            { label: 'Next accrual', value: `${getNextPayDate()} (+3.08h)` },
          ]}
        />

        <BalanceCard
          label="Sick Leave"
          available={16}
          used={8}
          total={40}
          unit="hours"
          color="orange"
          details={[
            { label: 'State', value: 'Illinois (1h per 40h worked)' },
            { label: 'Cap', value: '40h max balance' },
            { label: 'Carryover', value: '40h (state protected)' },
          ]}
        />

        <BalanceCard
          label="Unpaid Time (UPT)"
          available={20}
          used={0}
          total={20}
          unit="hours"
          color="green"
          details={[
            { label: 'Quarterly grant', value: '20h (last: Apr 1)' },
            { label: 'Next grant', value: `${getNextQuarterStart()} (+20h)` },
            { label: 'Warning', value: '0h balance = termination review' },
          ]}
        />

        <BalanceCard
          label="FMLA"
          available={480}
          used={0}
          total={480}
          unit="hours"
          color="purple"
          details={[
            { label: 'Eligible', value: 'Yes (14mo tenure, 1,560h worked)' },
            { label: 'Entitlement', value: '12 weeks (480h) per year' },
            { label: 'Year resets', value: `Jan 1, ${new Date().getFullYear() + 1}` },
          ]}
        />
      </div>

      {/* At-risk warning */}
      <div className="bg-yellow-950/50 border border-yellow-500/20 rounded-2xl p-5 shadow-elevation-1">
        <div className="flex items-center gap-2 mb-2">
          <svg className="w-5 h-5 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
          <span className="text-body-sm font-medium text-yellow-400">Hours At Risk</span>
        </div>
        <p className="text-body-sm text-gray-300">
          No hours at risk. Illinois state law protects accrued PTO from forfeiture.
        </p>
        <p className="text-xs text-gray-400 mt-1">
          {getDaysUntilYearEnd()} days until year-end. All balances carry over per state regulation.
        </p>
      </div>

      {/* Leave donation */}
      <div className="bg-surface-raised border border-white/[0.06] rounded-2xl p-5 shadow-elevation-1">
        <h3 className="text-body-sm font-medium mb-4">Leave Sharing</h3>
        <div className="grid grid-cols-2 gap-4 text-center">
          <div>
            <p className="text-heading-sm font-bold text-white">0h</p>
            <p className="text-xs text-gray-400 mt-1">Donated this year</p>
          </div>
          <div>
            <p className="text-heading-sm font-bold text-white">0h</p>
            <p className="text-xs text-gray-400 mt-1">Received this year</p>
          </div>
        </div>
        <button onClick={() => { const el = document.getElementById('donate-toast'); if(el) { el.classList.remove('hidden'); setTimeout(() => el.classList.add('hidden'), 3000) }}} className="w-full mt-4 border border-white/[0.1] active:bg-surface-highlight py-3.5 rounded-xl text-body-sm text-gray-300 transition press-scale">
          Donate Hours to a Colleague
        </button>
      </div>

      {/* Usage history */}
      <div>
        <h3 className="text-body-sm font-medium mb-3">Recent Usage</h3>
        <div className="space-y-2">
          <UsageRow date={daysAgo(11)} type="Sick" hours={8} desc="Unplanned callout" />
          <UsageRow date={`${daysAgo(29)}-${new Date(Date.now() - 27*86400000).getDate()}`} type="PTO" hours={24} desc="Family wedding" />
          <UsageRow date={daysAgo(43)} type="PTO" hours={8} desc="Holiday observed" />
          <UsageRow date={daysAgo(55)} type="Sick" hours={4} desc="Doctor appointment (half day)" />
        </div>
      </div>
    </div>
  )
}

function BalanceCard({ label, available, used, total, unit, color, details }: {
  label: string
  available: number
  used: number
  total: number
  unit: string
  color: string
  details: { label: string; value: string }[]
}) {
  const pct = Math.round((available / total) * 100)
  const colorMap: Record<string, { bar: string; text: string; border: string }> = {
    cyan: { bar: 'bg-cyan-500', text: 'text-cyan-400', border: 'border-t-cyan-500' },
    orange: { bar: 'bg-orange-500', text: 'text-orange-400', border: 'border-t-orange-500' },
    green: { bar: 'bg-green-500', text: 'text-green-400', border: 'border-t-green-500' },
    purple: { bar: 'bg-purple-500', text: 'text-purple-400', border: 'border-t-purple-500' },
  }
  const c = colorMap[color] || colorMap.cyan

  return (
    <div className={`bg-surface-raised border border-white/[0.06] border-t-2 ${c.border} rounded-2xl p-5 shadow-elevation-1`}>
      <div className="flex items-center justify-between mb-3">
        <span className="text-body-sm font-medium">{label}</span>
        <span className={`text-heading-sm font-bold ${c.text}`}>{available}{unit === 'hours' ? 'h' : 'd'}</span>
      </div>

      {/* Progress bar */}
      <div className="w-full h-2.5 bg-surface-highlight rounded-full overflow-hidden shadow-inner-soft mb-2">
        <div className={`h-full ${c.bar} rounded-full relative`} style={{ width: `${pct}%` }}>
          <div className="absolute inset-0 progress-shimmer rounded-full"></div>
        </div>
      </div>
      <div className="flex justify-between text-xs text-gray-400 mb-4">
        <span>{used}{unit === 'hours' ? 'h' : 'd'} used</span>
        <span>{available}/{total}{unit === 'hours' ? 'h' : 'd'} remaining</span>
      </div>

      {/* Details */}
      <div className="space-y-2">
        {details.map((d, i) => (
          <div key={i} className="flex items-center justify-between text-xs">
            <span className="text-gray-400">{d.label}</span>
            <span className="text-gray-300">{d.value}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function UsageRow({ date, type, hours, desc }: { date: string; type: string; hours: number; desc: string }) {
  return (
    <div className="flex items-center justify-between bg-surface-raised border border-white/[0.06] rounded-xl px-4 py-3.5 shadow-elevation-1">
      <div className="flex items-center gap-4">
        <div className="text-center w-16 flex-shrink-0">
          <p className="text-xs text-gray-300">{date}</p>
        </div>
        <div>
          <p className="text-body-sm font-medium">{desc}</p>
          <p className="text-xs text-gray-400">{type}</p>
        </div>
      </div>
      <span className="text-body-sm text-red-400 font-semibold">-{hours}h</span>
    </div>
  )
}
