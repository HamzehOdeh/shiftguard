export default function WorkerLoading() {
  return (
    <div className="px-4 py-5 space-y-5 animate-fade-in">
      {/* Greeting skeleton */}
      <div>
        <div className="skeleton h-6 w-48 mb-2"></div>
        <div className="skeleton h-4 w-32"></div>
      </div>

      {/* Notification skeleton */}
      <div className="space-y-2">
        <div className="skeleton h-20 w-full rounded-lg"></div>
        <div className="skeleton h-16 w-full rounded-lg"></div>
      </div>

      {/* Today's shift skeleton */}
      <div className="skeleton h-24 w-full rounded-xl"></div>

      {/* Hours skeleton */}
      <div className="skeleton h-20 w-full rounded-xl"></div>

      {/* Quick actions skeleton */}
      <div className="grid grid-cols-2 gap-3">
        <div className="skeleton h-[88px] w-full rounded-xl"></div>
        <div className="skeleton h-[88px] w-full rounded-xl"></div>
        <div className="skeleton h-[88px] w-full rounded-xl"></div>
        <div className="skeleton h-[88px] w-full rounded-xl"></div>
      </div>
    </div>
  )
}
