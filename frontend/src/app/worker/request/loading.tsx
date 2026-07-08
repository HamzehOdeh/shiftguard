export default function RequestLoading() {
  return (
    <div className="px-4 py-5 space-y-4 animate-fade-in">
      <div className="skeleton h-7 w-44 rounded-lg"></div>
      <div className="skeleton h-10 w-full rounded-lg"></div>
      <div className="skeleton h-32 w-full rounded-xl"></div>
      <div className="skeleton h-32 w-full rounded-xl"></div>
      <div className="skeleton h-12 w-full rounded-lg"></div>
    </div>
  )
}
