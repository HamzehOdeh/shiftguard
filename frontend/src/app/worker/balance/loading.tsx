export default function BalanceLoading() {
  return (
    <div className="px-5 py-6 space-y-5">
      <div className="skeleton h-7 w-40 rounded-2xl"></div>
      <div className="grid grid-cols-2 gap-3">
        <div className="skeleton h-36 rounded-2xl"></div>
        <div className="skeleton h-36 rounded-2xl"></div>
        <div className="skeleton h-36 rounded-2xl"></div>
        <div className="skeleton h-36 rounded-2xl"></div>
      </div>
      <div className="skeleton h-28 w-full rounded-2xl"></div>
      <div className="skeleton h-44 w-full rounded-2xl"></div>
    </div>
  )
}
