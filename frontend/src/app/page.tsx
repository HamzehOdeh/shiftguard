export default function Home() {
  return (
    <div className="min-h-screen">
      {/* Hero */}
      <header className="border-b border-gray-800">
        <nav className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <img src="/logo.png" alt="ShiftGuard" className="h-8" />
          </div>
          <div className="flex items-center gap-6">
            <a href="/calculator" className="text-gray-400 hover:text-white transition">Free Calculator</a>
            <a href="/demo" className="text-gray-400 hover:text-white transition">Live Demo</a>
            <a href="/reporting" className="text-gray-400 hover:text-white transition">ROI Dashboard</a>
            <a href="/login" className="bg-brand-600 hover:bg-brand-700 px-4 py-2 rounded-lg transition font-medium">Sign In</a>
          </div>
        </nav>
      </header>

      <main className="max-w-7xl mx-auto px-6">
        {/* Hero Section */}
        <section className="py-20 text-center">
          <h1 className="text-5xl md:text-6xl font-bold mb-6 leading-tight">
            Know your compliance risk<br />
            <span className="text-danger">in dollars</span><br />
            before you publish the schedule.
          </h1>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto mb-10">
            AI-powered workforce compliance that catches violations before they happen.
            Works in 60 seconds. No 6-month implementation.
          </p>
          <div className="flex gap-4 justify-center">
            <a href="/demo" className="bg-brand-600 hover:bg-brand-700 px-8 py-4 rounded-lg text-lg font-semibold transition">
              Try the Demo (Free)
            </a>
            <a href="/calculator" className="border border-gray-600 hover:border-brand-500 px-8 py-4 rounded-lg text-lg transition">
              Calculate My Risk
            </a>
          </div>
        </section>

        {/* Social Proof Numbers */}
        <section className="py-12 border-t border-gray-800">
          <div className="grid grid-cols-4 gap-8 text-center">
            <div>
              <div className="text-3xl font-bold text-brand-500">88+</div>
              <div className="text-gray-400 text-sm">Compliance Rules</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-brand-500">14</div>
              <div className="text-gray-400 text-sm">Jurisdictions</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-brand-500">60s</div>
              <div className="text-gray-400 text-sm">Time to First Insight</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-brand-500">$0</div>
              <div className="text-gray-400 text-sm">To Try</div>
            </div>
          </div>
        </section>

        {/* Industry Selection */}
        <section className="py-20 border-t border-gray-800">
          <h2 className="text-3xl font-bold text-center mb-4">Purpose-built for your industry</h2>
          <p className="text-center text-gray-400 mb-12">Same powerful platform. Tailored to how your industry actually works.</p>
          <div className="grid md:grid-cols-5 gap-4">
            <IndustryLink href="/healthcare" name="Healthcare" detail="Hospitals, clinics, nursing" />
            <IndustryLink href="/warehouse" name="Warehousing" detail="FCs, distribution, logistics" />
            <IndustryLink href="/retail" name="Retail" detail="Stores, multi-location" />
            <IndustryLink href="/hospitality" name="Hospitality" detail="Hotels, restaurants, F&B" />
            <IndustryLink href="/manufacturing" name="Manufacturing" detail="Plants, production, assembly" />
          </div>
        </section>

        {/* Features Grid */}
        <section className="py-20 border-t border-gray-800">
          <h2 className="text-3xl font-bold text-center mb-12">Everything you need. Nothing you don't.</h2>
          <div className="grid md:grid-cols-3 gap-8">
            <FeatureCard
              title="AI Scheduling Assistant"
              description="Just ask: 'Who can cover tomorrow?' or 'Generate next month's schedule with fairness.' The AI handles it."
              badge="Differentiator"
            />
            <FeatureCard
              title="Penalty $ Exposure"
              description="See the exact dollar cost of every violation before you publish. No competitor shows you this."
              badge="Unique"
            />
            <FeatureCard
              title="Self-Healing Schedules"
              description="Callout at 5am? System finds coverage automatically. Manager wakes up to 'Resolved.'"
              badge="Differentiator"
            />
            <FeatureCard
              title="Fairness Engine"
              description="Equal distribution of nights, weekends, holidays. Workers trust it because it's visibly fair."
            />
            <FeatureCard
              title="Worker Self-Service"
              description="Workers request time off, set preferences, accept VET — all from their phone. 80% auto-approved."
            />
            <FeatureCard
              title="Multi-Jurisdiction"
              description="US (Chicago, CA, NYC, OR) + International (EU, UK, Germany, France, UAE, Australia). 88+ rules."
            />
          </div>
        </section>

        {/* Comparison */}
        <section className="py-20 border-t border-gray-800">
          <h2 className="text-3xl font-bold text-center mb-4">Why ShiftGuard vs. the status quo</h2>
          <p className="text-center text-gray-400 mb-12">UKG takes 6 months. We take 60 seconds.</p>
          <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            <div className="p-6 bg-red-950/30 border border-red-900/50 rounded-xl">
              <h3 className="text-lg font-bold text-red-400 mb-4">Without ShiftGuard</h3>
              <ul className="space-y-3 text-gray-300">
                <li>Violations found AFTER fines arrive</li>
                <li>Manager spends 45min per callout scrambling</li>
                <li>Workers complain schedule is unfair</li>
                <li>$50K-500K annual penalty exposure</li>
                <li>6-month implementation for enterprise tools</li>
              </ul>
            </div>
            <div className="p-6 bg-green-950/30 border border-green-900/50 rounded-xl">
              <h3 className="text-lg font-bold text-green-400 mb-4">With ShiftGuard</h3>
              <ul className="space-y-3 text-gray-300">
                <li>Violations caught BEFORE publishing</li>
                <li>Callouts self-heal in 3-5 minutes</li>
                <li>Fairness is provable and transparent</li>
                <li>Penalty exposure drops to near-zero</li>
                <li>Working in 60 seconds with a CSV</li>
              </ul>
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="py-20 text-center border-t border-gray-800">
          <h2 className="text-4xl font-bold mb-4">See your compliance risk in 60 seconds</h2>
          <p className="text-gray-400 text-lg mb-8">No signup. No sales call. Just answers.</p>
          <a href="/calculator" className="bg-brand-600 hover:bg-brand-700 px-10 py-5 rounded-lg text-xl font-semibold transition inline-block">
            Calculate My Risk (Free)
          </a>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-800 py-8 text-center text-gray-500 text-sm">
        ShiftGuard - AI-Powered Workforce Compliance &middot; Schedule with confidence.
      </footer>
    </div>
  )
}

function FeatureCard({ title, description, badge }: { title: string, description: string, badge?: string }) {
  return (
    <div className="p-6 bg-gray-900 border border-gray-800 rounded-xl hover:border-brand-600 transition">
      {badge && (
        <span className="text-xs bg-brand-900 text-brand-500 px-2 py-1 rounded-full font-medium">{badge}</span>
      )}
      <h3 className="text-lg font-bold mt-3 mb-2">{title}</h3>
      <p className="text-gray-400 text-sm">{description}</p>
    </div>
  )
}

function IndustryLink({ href, name, detail }: { href: string, name: string, detail: string }) {
  return (
    <a href={href} className="p-5 bg-gray-900 border border-gray-800 rounded-xl hover:border-brand-500 transition text-center group">
      <h3 className="font-bold group-hover:text-brand-500 transition">{name}</h3>
      <p className="text-gray-500 text-xs mt-1">{detail}</p>
    </a>
  )
}
