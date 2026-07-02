export default function HealthcarePage() {
  return (
    <div className="min-h-screen">
      <header className="border-b border-gray-800">
        <nav className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <img src="/logo.png" alt="ShiftGuard" className="h-8" />
            <span className="text-sm text-brand-500 font-medium">for Healthcare</span>
          </div>
          <div className="flex items-center gap-6">
            <a href="/healthcare#features" className="text-gray-400 hover:text-white transition">Features</a>
            <a href="/calculator" className="text-gray-400 hover:text-white transition">Cost Calculator</a>
            <a href="/login" className="bg-brand-600 hover:bg-brand-700 px-4 py-2 rounded-lg transition font-medium">Sign In</a>
          </div>
        </nav>
      </header>

      <main className="max-w-7xl mx-auto px-6">
        <section className="py-20 text-center">
          <p className="text-brand-500 font-medium mb-4">Built for hospitals, clinics, and health systems</p>
          <h1 className="text-5xl md:text-6xl font-bold mb-6 leading-tight">
            Stop scheduling residents<br />
            into <span className="text-danger">ACGME violations.</span>
          </h1>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto mb-10">
            ShiftGuard catches duty hour violations, clopening risks, and nurse ratio gaps
            before you publish the schedule. AI-powered. Works in 60 seconds.
          </p>
          <div className="flex gap-4 justify-center">
            <a href="/demo?industry=healthcare" className="bg-brand-600 hover:bg-brand-700 px-8 py-4 rounded-lg text-lg font-semibold transition">
              See Healthcare Demo
            </a>
            <a href="/calculator" className="border border-gray-600 hover:border-brand-500 px-8 py-4 rounded-lg text-lg transition">
              Calculate My Penalty Exposure
            </a>
          </div>
        </section>

        <section className="py-12 border-t border-gray-800">
          <div className="grid grid-cols-4 gap-8 text-center">
            <div>
              <div className="text-3xl font-bold text-brand-500">ACGME</div>
              <div className="text-gray-400 text-sm">Duty Hour Compliance</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-brand-500">RN Ratios</div>
              <div className="text-gray-400 text-sm">Nurse-to-Patient Staffing</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-brand-500">FMLA</div>
              <div className="text-gray-400 text-sm">Auto-Triggered Notifications</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-brand-500">Fair</div>
              <div className="text-gray-400 text-sm">Equal Nights & Holidays</div>
            </div>
          </div>
        </section>

        <section className="py-20 border-t border-gray-800" id="features">
          <h2 className="text-3xl font-bold text-center mb-12">Built for how hospitals actually work</h2>
          <div className="grid md:grid-cols-3 gap-8">
            <FeatureCard
              title="Residency Program Scheduling"
              description="Generate fair annual rotations for PGY-1 through Fellow. Equal nights, weekends, holidays. ACGME 80-hour rule enforced automatically."
            />
            <FeatureCard
              title="Nursing by Unit"
              description="Each nurse manager schedules their own unit. ED nursing is separate from ICU. Charge nurses, staff RNs, CNAs — each team independent."
            />
            <FeatureCard
              title="Self-Healing Callouts"
              description="RN calls out at 5am? System finds coverage from the same unit first, then same department, then float pool. Manager wakes up to 'Resolved.'"
            />
            <FeatureCard
              title="Fatigue Science"
              description="Not just hour counting — circadian-based crash risk scoring. Flags when a nurse after 4 consecutive nights is at impairment equivalent to BAC 0.05."
            />
            <FeatureCard
              title="Credential Tracking"
              description="Auto-blocks scheduling if BLS, ACLS, or nursing license expires before shift date. Pushes renewal reminders 60/30/7 days out."
            />
            <FeatureCard
              title="Department Isolation"
              description="Residency director sees only residents. Nurse manager sees only their unit. ED director sees all. HIPAA-adjacent data protection built in."
            />
          </div>
        </section>

        <section className="py-20 border-t border-gray-800">
          <h2 className="text-3xl font-bold text-center mb-4">Why hospitals switch to ShiftGuard</h2>
          <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto mt-12">
            <div className="p-6 bg-red-950/30 border border-red-900/50 rounded-xl">
              <h3 className="text-lg font-bold text-red-400 mb-4">Without ShiftGuard</h3>
              <ul className="space-y-3 text-gray-300">
                <li>Residents hit 80+ hours — program citation risk</li>
                <li>Nurse manager spends 2 hours/day on schedule changes</li>
                <li>Night shifts always fall on the same 2 people</li>
                <li>FMLA notification missed — $50K+ lawsuit exposure</li>
                <li>Callout at 5am = 45 minutes of phone calls</li>
              </ul>
            </div>
            <div className="p-6 bg-green-950/30 border border-green-900/50 rounded-xl">
              <h3 className="text-lg font-bold text-green-400 mb-4">With ShiftGuard</h3>
              <ul className="space-y-3 text-gray-300">
                <li>ACGME hours tracked in real-time with countdown</li>
                <li>AI generates fair rotation in seconds</li>
                <li>Nights distributed provably equally (scorecard)</li>
                <li>FMLA auto-triggered after 3+ consecutive days</li>
                <li>Callouts self-heal in 3-5 minutes</li>
              </ul>
            </div>
          </div>
        </section>

        <section className="py-20 text-center border-t border-gray-800">
          <h2 className="text-4xl font-bold mb-4">See it work with your schedule</h2>
          <p className="text-gray-400 text-lg mb-8">Upload a CSV or try our healthcare demo. 60 seconds to first insight.</p>
          <a href="/demo?industry=healthcare" className="bg-brand-600 hover:bg-brand-700 px-10 py-5 rounded-lg text-xl font-semibold transition inline-block">
            Try Healthcare Demo (Free)
          </a>
        </section>
      </main>

      <footer className="border-t border-gray-800 py-8 text-center text-gray-500 text-sm">
        ShiftGuard for Healthcare &middot; ACGME compliant scheduling &middot; AI-powered
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
