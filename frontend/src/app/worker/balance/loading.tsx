export default function BalanceLoading() {
  return (
    <div className="px-4 py-5 space-y-4 animate-fade-in">
      <div className="skeleton h-7 w-36 rounded-lg"></div>
      <div className="grid grid-cols-2 gap-3">
        <div className="skeleton h-28 rounded-xl"></div>
        <div className="skeleton h-28 rounded-xl"></div>
        <div className="skeleton h-28 rounded-xl"></div>
        <div className="skeleton h-28 rounded-xl"></div>
      </div>
      <div className="skeleton h-24 w-full rounded-xl"></div>
      <div className="skeleton h-40 w-full rounded-xl"></div>
    </div>
  )
}
