export default function WorkerLoading() {
  return (
    <div className="px-5 py-6 space-y-6">
      <div>
        <div className="skeleton h-7 w-52 mb-2"></div>
        <div className="skeleton h-5 w-36"></div>
      </div>
      <div className="space-y-3">
        <div className="skeleton h-24 w-full rounded-2xl"></div>
        <div className="skeleton h-20 w-full rounded-2xl"></div>
      </div>
      <div className="skeleton h-28 w-full rounded-2xl"></div>
      <div className="skeleton h-24 w-full rounded-2xl"></div>
      <div className="grid grid-cols-2 gap-3">
        <div className="skeleton h-[100px] w-full rounded-2xl"></div>
        <div className="skeleton h-[100px] w-full rounded-2xl"></div>
        <div className="skeleton h-[100px] w-full rounded-2xl"></div>
        <div className="skeleton h-[100px] w-full rounded-2xl"></div>
      </div>
    </div>
  )
}
