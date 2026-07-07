export function KPICard({ label, value, trend, trendUp }: {
  label: string
  value: string
  trend?: string
  trendUp?: boolean
}) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className="text-2xl font-bold">{value}</p>
      {trend && (
        <p className={`text-xs mt-1 ${trendUp ? 'text-green-400' : 'text-red-400'}`}>
          {trend} vs last month
        </p>
      )}
    </div>
  )
}
