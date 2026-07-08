export default function ScheduleLoading() {
  return (
    <div className="px-5 py-6 space-y-5">
      <div className="grid grid-cols-3 gap-3">
        <div className="skeleton h-16 rounded-2xl"></div>
        <div className="skeleton h-16 rounded-2xl"></div>
        <div className="skeleton h-16 rounded-2xl"></div>
      </div>
      <div className="skeleton h-8 w-48 mx-auto rounded-2xl"></div>
      <div className="skeleton h-[320px] w-full rounded-2xl"></div>
    </div>
  )
}
