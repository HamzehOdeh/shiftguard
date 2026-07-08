'use client'

export default function WorkerBalancePage() {
  return (
    <div className="px-4 py-5 space-y-5">
      <h1 className="text-xl font-bold">My Leave Balances</h1>

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
            { label: 'Next accrual', value: 'Jul 15 (+3.08h)' },
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
            { label: 'Next grant', value: 'Jul 1 (+20h)' },
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
            { label: 'Year resets', value: 'Jan 1, 2027' },
          ]}
        />
      </div>

      {/* At-risk warning */}
      <div className="bg-yellow-950 border border-yellow-800 rounded-xl p-4">
        <div className="flex items-center gap-2 mb-2">
          <svg className="w-5 h-5 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
          <span className="text-sm font-medium text-yellow-400">Hours At Risk</span>
        </div>
        <p className="text-sm text-gray-300">
          No hours at risk. Illinois state law protects accrued PTO from forfeiture.
        </p>
        <p className="text-[10px] text-gray-500 mt-1">
          178 days until year-end. All balances carry over per state regulation.
        </p>
      </div>

      {/* Leave donation */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
        <h3 className="text-sm font-medium mb-3">Leave Sharing</h3>
        <div className="grid grid-cols-2 gap-3 text-center">
          <div>
            <p className="text-lg font-bold text-white">0h</p>
            <p className="text-[10px] text-gray-500">Donated this year</p>
          </div>
          <div>
            <p className="text-lg font-bold text-white">0h</p>
            <p className="text-[10px] text-gray-500">Received this year</p>
          </div>
        </div>
        <button onClick={() => alert('Leave donation request submitted to HR for approval. Your colleague will be notified.')} className="w-full mt-3 border border-gray-700 hover:border-gray-500 py-2 rounded-lg text-sm text-gray-300 transition">
          Donate Hours to a Colleague
        </button>
      </div>

      {/* Usage history */}
      <div>
        <h3 className="text-sm font-medium mb-3">Recent Usage</h3>
        <div className="space-y-2">
          <UsageRow date="Jun 28" type="Sick" hours={8} desc="Unplanned callout" />
          <UsageRow date="Jun 10-12" type="PTO" hours={24} desc="Family wedding" />
          <UsageRow date="May 27" type="PTO" hours={8} desc="Memorial Day observed" />
          <UsageRow date="May 15" type="Sick" hours={4} desc="Doctor appointment (half day)" />
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
  const colorMap: Record<string, { bar: string; text: string; bg: string }> = {
    cyan: { bar: 'bg-cyan-500', text: 'text-cyan-400', bg: 'bg-cyan-950' },
    orange: { bar: 'bg-orange-500', text: 'text-orange-400', bg: 'bg-orange-950' },
    green: { bar: 'bg-green-500', text: 'text-green-400', bg: 'bg-green-950' },
    purple: { bar: 'bg-purple-500', text: 'text-purple-400', bg: 'bg-purple-950' },
  }
  const c = colorMap[color] || colorMap.cyan

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium">{label}</span>
        <span className={`text-lg font-bold ${c.text}`}>{available}{unit === 'hours' ? 'h' : 'd'}</span>
      </div>

      {/* Progress bar */}
      <div className="w-full h-2 bg-gray-800 rounded-full overflow-hidden mb-1">
        <div className={`h-full ${c.bar} rounded-full`} style={{ width: `${pct}%` }}></div>
      </div>
      <div className="flex justify-between text-[10px] text-gray-500 mb-3">
        <span>{used}{unit === 'hours' ? 'h' : 'd'} used</span>
        <span>{available}/{total}{unit === 'hours' ? 'h' : 'd'} remaining</span>
      </div>

      {/* Details */}
      <div className="space-y-1">
        {details.map((d, i) => (
          <div key={i} className="flex items-center justify-between text-xs">
            <span className="text-gray-500">{d.label}</span>
            <span className="text-gray-300">{d.value}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function UsageRow({ date, type, hours, desc }: { date: string; type: string; hours: number; desc: string }) {
  return (
    <div className="flex items-center justify-between bg-gray-900 border border-gray-800 rounded-lg px-3 py-2.5">
      <div className="flex items-center gap-3">
        <div className="text-center w-12">
          <p className="text-xs text-gray-400">{date}</p>
        </div>
        <div>
          <p className="text-sm font-medium">{desc}</p>
          <p className="text-[10px] text-gray-500">{type}</p>
        </div>
      </div>
      <span className="text-sm text-red-400 font-medium">-{hours}h</span>
    </div>
  )
}
