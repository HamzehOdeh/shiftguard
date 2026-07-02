export default function ManufacturingPage() {
  return (
    <div className="min-h-screen">
      <header className="border-b border-gray-800">
        <nav className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <img src="/logo.png" alt="ShiftGuard" className="h-8" />
            <span className="text-sm text-brand-500 font-medium">for Manufacturing</span>
          </div>
          <div className="flex items-center gap-6">
            <a href="/calculator" className="text-gray-400 hover:text-white transition">Cost Calculator</a>
            <a href="/login" className="bg-brand-600 hover:bg-brand-700 px-4 py-2 rounded-lg transition font-medium">Sign In</a>
          </div>
        </nav>
      </header>

      <main className="max-w-7xl mx-auto px-6">
        <section className="py-20 text-center">
          <p className="text-brand-500 font-medium mb-4">Built for plants, production lines, and assembly operations</p>
          <h1 className="text-5xl md:text-6xl font-bold mb-6 leading-tight">
            Fatigue kills productivity<br />
            <span className="text-danger">and people.</span>
          </h1>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto mb-10">
            ShiftGuard uses circadian science to prevent dangerous fatigue on the floor.
            Rotation optimization, consecutive day limits, CBA grievance-proofing, and
            Oregon predictive scheduling — all in one platform.
          </p>
          <div className="flex gap-4 justify-center">
            <a href="/demo?industry=manufacturing" className="bg-brand-600 hover:bg-brand-700 px-8 py-4 rounded-lg text-lg font-semibold transition">
              See Manufacturing Demo
            </a>
            <a href="/calculator" className="border border-gray-600 hover:border-brand-500 px-8 py-4 rounded-lg text-lg transition">
              Calculate My Penalty Exposure
            </a>
          </div>
        </section>

        <section className="py-20 border-t border-gray-800">
          <h2 className="text-3xl font-bold text-center mb-12">Production never stops. Your compliance shouldn't either.</h2>
          <div className="grid md:grid-cols-3 gap-8">
            <FeatureCard
              title="Fatigue Science (SAFTE Model)"
              description="Real circadian modeling — not just hour counting. Predicts crash risk, recommends rotation direction, calculates recovery time needed after night blocks."
            />
            <FeatureCard
              title="CBA Grievance-Proof"
              description="Consecutive day limits, equitable OT distribution, seniority-based assignment, mandatory rest periods — all CBA rules enforced automatically."
            />
            <FeatureCard
              title="2-Shift & 3-Shift Patterns"
              description="Day/night, continental, 2-2-3, fixed permanent — any rotation pattern. Forward rotation recommended for health. System models all of them."
            />
            <FeatureCard
              title="Maintenance Scheduling"
              description="Electricians, PLC techs, mechanics — separate from production but coordinated. Coverage for shutdown periods and emergency calls."
            />
            <FeatureCard
              title="Oregon Predictive Scheduling"
              description="If you operate in Oregon: advance notice, schedule change premiums, right-to-rest — all caught before posting."
            />
            <FeatureCard
              title="Certification Blocking"
              description="Forklift cert expired? Machine operator license lapsed? System blocks scheduling and pushes renewal reminders automatically."
            />
          </div>
        </section>

        <section className="py-20 text-center border-t border-gray-800">
          <h2 className="text-4xl font-bold mb-4">Keep your line running. Keep your people safe.</h2>
          <p className="text-gray-400 text-lg mb-8">Fatigue science + compliance + fairness. All in one platform.</p>
          <a href="/demo?industry=manufacturing" className="bg-brand-600 hover:bg-brand-700 px-10 py-5 rounded-lg text-xl font-semibold transition inline-block">
            Try Manufacturing Demo (Free)
          </a>
        </section>
      </main>

      <footer className="border-t border-gray-800 py-8 text-center text-gray-500 text-sm">
        ShiftGuard for Manufacturing &middot; Fatigue-safe scheduling &middot; AI-powered
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
