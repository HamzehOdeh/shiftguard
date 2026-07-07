export function NavHeader({ showDemo = true }: { showDemo?: boolean }) {
  return (
    <header className="border-b border-gray-800 px-6 py-4">
      <div className="max-w-6xl mx-auto flex items-center justify-between">
        <a href="/" className="flex items-center gap-2">
          <div className="w-8 h-8 bg-brand-500 rounded-lg flex items-center justify-center text-sm font-bold text-white">SG</div>
          <span className="font-semibold text-white">ShiftGuard</span>
        </a>
        <div className="flex items-center gap-3">
          {showDemo && (
            <a href="/demo" className="text-sm text-gray-400 hover:text-white transition">Demo</a>
          )}
          <a href="/calculator" className="text-sm text-gray-400 hover:text-white transition">Calculator</a>
          <a href="/login" className="text-sm bg-brand-600 hover:bg-brand-700 px-4 py-2 rounded-lg transition text-white">Sign In</a>
        </div>
      </div>
    </header>
  )
}
