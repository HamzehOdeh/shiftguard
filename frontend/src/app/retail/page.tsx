export default function RetailPage() {
  return (
    <div className="min-h-screen">
      <header className="border-b border-gray-800">
        <nav className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <img src="/logo.png" alt="ShiftGuard" className="h-8" />
            <span className="text-sm text-brand-500 font-medium">for Retail</span>
          </div>
          <div className="flex items-center gap-6">
            <a href="/calculator" className="text-gray-400 hover:text-white transition">Cost Calculator</a>
            <a href="/login" className="bg-brand-600 hover:bg-brand-700 px-4 py-2 rounded-lg transition font-medium">Sign In</a>
          </div>
        </nav>
      </header>

      <main className="max-w-7xl mx-auto px-6">
        <section className="py-20 text-center">
          <p className="text-brand-500 font-medium mb-4">Built for multi-location retail and store operations</p>
          <h1 className="text-5xl md:text-6xl font-bold mb-6 leading-tight">
            Every schedule change<br />
            costs you <span className="text-danger">$300-500.</span>
          </h1>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto mb-10">
            Chicago Fair Workweek, NYC predictive scheduling, Oregon advance notice —
            ShiftGuard catches violations before they cost you. Works across all your locations.
          </p>
          <div className="flex gap-4 justify-center">
            <a href="/demo?industry=retail" className="bg-brand-600 hover:bg-brand-700 px-8 py-4 rounded-lg text-lg font-semibold transition">
              See Retail Demo
            </a>
            <a href="/calculator" className="border border-gray-600 hover:border-brand-500 px-8 py-4 rounded-lg text-lg transition">
              Calculate My Penalty Exposure
            </a>
          </div>
        </section>

        <section className="py-20 border-t border-gray-800">
          <h2 className="text-3xl font-bold text-center mb-12">Multi-location. Multi-jurisdiction. One platform.</h2>
          <div className="grid md:grid-cols-3 gap-8">
            <FeatureCard
              title="Fair Workweek Compliance"
              description="14-day advance notice, predictability pay, right-to-rest — enforced automatically for Chicago, NYC, Oregon, Seattle, and more."
            />
            <FeatureCard
              title="Clopening Detection"
              description="Associate closes at 10:30pm then opens at 5:30am? Blocked. System suggests alternatives before you publish."
            />
            <FeatureCard
              title="Minor Restrictions"
              description="Auto-enforces hour caps and time restrictions for under-18 workers. No manual tracking needed."
            />
            <FeatureCard
              title="Multi-Store View"
              description="District manager sees all locations. Store manager sees only their store. Associates see only their schedule."
            />
            <FeatureCard
              title="Shift Marketplace"
              description="Associates can pick up open shifts, propose swaps, and set preferences — all compliance-checked automatically before approval."
            />
            <FeatureCard
              title="Foot Traffic Demand"
              description="POS volume up? System recommends additional coverage. Slow Tuesday? Offer VTO before you're overstaffed."
            />
          </div>
        </section>

        <section className="py-20 text-center border-t border-gray-800">
          <h2 className="text-4xl font-bold mb-4">Stop paying predictability penalties</h2>
          <p className="text-gray-400 text-lg mb-8">Every last-minute schedule change is $300-500. See how much you are exposed to.</p>
          <a href="/demo?industry=retail" className="bg-brand-600 hover:bg-brand-700 px-10 py-5 rounded-lg text-xl font-semibold transition inline-block">
            Try Retail Demo (Free)
          </a>
        </section>
      </main>

      <footer className="border-t border-gray-800 py-8 text-center text-gray-500 text-sm">
        ShiftGuard for Retail &middot; Fair Workweek compliant &middot; AI-powered
      </footer>
    </div>
  )
}

function FeatureCard({ title, description }: { title: string, description: string }) {
  return (
    <div className="p-6 bg-gray-900 border border-gray-800 rounded-xl">
      <h3 className="text-lg font-bold mt-2 mb-2">{title}</h3>
      <p className="text-gray-400 text-sm">{description}</p>
    </div>
  )
}
