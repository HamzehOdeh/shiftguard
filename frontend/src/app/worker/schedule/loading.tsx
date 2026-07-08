export default function ScheduleLoading() {
  return (
    <div className="px-4 py-5 space-y-4 animate-fade-in">
      {/* Balance bar */}
      <div className="grid grid-cols-3 gap-2">
        <div className="skeleton h-14 rounded-lg"></div>
        <div className="skeleton h-14 rounded-lg"></div>
        <div className="skeleton h-14 rounded-lg"></div>
      </div>
      {/* Month header */}
      <div className="skeleton h-8 w-48 mx-auto rounded-lg"></div>
      {/* Calendar grid */}
      <div className="grid grid-cols-7 gap-1">
        {Array.from({ length: 35 }).map((_, i) => (
          <div key={i} className="skeleton h-11 rounded-lg"></div>
        ))}
      </div>
    </div>
  )
}
