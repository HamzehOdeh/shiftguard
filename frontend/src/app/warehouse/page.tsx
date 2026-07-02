export default function WarehousePage() {
  return (
    <div className="min-h-screen">
      <header className="border-b border-gray-800">
        <nav className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <img src="/logo.png" alt="ShiftGuard" className="h-8" />
            <span className="text-sm text-brand-500 font-medium">for Warehousing</span>
          </div>
          <div className="flex items-center gap-6">
            <a href="/warehouse#features" className="text-gray-400 hover:text-white transition">Features</a>
            <a href="/calculator" className="text-gray-400 hover:text-white transition">Cost Calculator</a>
            <a href="/login" className="bg-brand-600 hover:bg-brand-700 px-4 py-2 rounded-lg transition font-medium">Sign In</a>
          </div>
        </nav>
      </header>

      <main className="max-w-7xl mx-auto px-6">
        <section className="py-20 text-center">
          <p className="text-brand-500 font-medium mb-4">Built for fulfillment centers, distribution, and logistics</p>
          <h1 className="text-5xl md:text-6xl font-bold mb-6 leading-tight">
            Your DA5 shift code<br />
            just got <span className="text-brand-500">intelligent.</span>
          </h1>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto mb-10">
            ShiftGuard manages fixed shift templates, VET/MET fairness, Chicago Fair Workweek compliance,
            and callout coverage — all from one platform. Understands front-half, back-half, and everything in between.
          </p>
          <div className="flex gap-4 justify-center">
            <a href="/demo?industry=warehouse" className="bg-brand-600 hover:bg-brand-700 px-8 py-4 rounded-lg text-lg font-semibold transition">
              See Warehouse Demo
            </a>
            <a href="/calculator" className="border border-gray-600 hover:border-brand-500 px-8 py-4 rounded-lg text-lg transition">
              Calculate My Penalty Exposure
            </a>
          </div>
        </section>

        <section className="py-12 border-t border-gray-800">
          <div className="grid grid-cols-4 gap-8 text-center">
            <div>
              <div className="text-3xl font-bold text-brand-500">VET/MET</div>
              <div className="text-gray-400 text-sm">Fair Distribution</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-brand-500">DA5/NB1</div>
              <div className="text-gray-400 text-sm">Fixed Shift Codes</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-brand-500">60hr</div>
              <div className="text-gray-400 text-sm">Cap Enforcement</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-brand-500">3min</div>
              <div className="text-gray-400 text-sm">Callout Self-Heal</div>
            </div>
          </div>
        </section>

        <section className="py-20 border-t border-gray-800" id="features">
          <h2 className="text-3xl font-bold text-center mb-12">Built for how FCs actually operate</h2>
          <div className="grid md:grid-cols-3 gap-8">
            <FeatureCard
              title="Fixed Shift Templates"
              description="DA5-0700-IB, NB1-1800-OB — define your shift codes once, assign AAs permanently. System handles coverage when someone is out."
            />
            <FeatureCard
              title="VET Fairness Engine"
              description="VET offered to people who declared availability FIRST, then fairness-ranked. No more 'same 3 people always get asked.' Tracks who's been offered, accepted, declined."
            />
            <FeatureCard
              title="MET Distribution"
              description="When VET doesn't fill the gap, MET is assigned fairly — rotating by who's had the least mandatory extra time. CBA grievance-proof."
            />
            <FeatureCard
              title="Chicago Fair Workweek"
              description="14-day advance notice, predictability pay, clopening detection, right-to-rest — all enforced before the schedule posts. $300-500/violation avoided."
            />
            <FeatureCard
              title="Self-Healing Callouts"
              description="AA calls out → system checks who declared available → offers VET → if no takers, broadcasts to all → first accept wins. Manager sees: 'Resolved.'"
            />
            <FeatureCard
              title="UPT / Attendance Tracking"
              description="Live UPT balance per AA. Warning at 4 hours. Critical alert at 0. Pattern detection for Monday callouts and payday absences."
            />
          </div>
        </section>

        <section className="py-20 text-center border-t border-gray-800">
          <h2 className="text-4xl font-bold mb-4">See it handle your shift codes</h2>
          <p className="text-gray-400 text-lg mb-8">Works with your existing DA/NB/DC patterns. 60 seconds to first insight.</p>
          <a href="/demo?industry=warehouse" className="bg-brand-600 hover:bg-brand-700 px-10 py-5 rounded-lg text-xl font-semibold transition inline-block">
            Try Warehouse Demo (Free)
          </a>
        </section>
      </main>

      <footer className="border-t border-gray-800 py-8 text-center text-gray-500 text-sm">
        ShiftGuard for Warehousing &middot; Fair Workweek compliant &middot; AI-powered
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
