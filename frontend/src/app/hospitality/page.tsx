export default function HospitalityPage() {
  return (
    <div className="min-h-screen">
      <header className="border-b border-gray-800">
        <nav className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <img src="/logo.png" alt="ShiftGuard" className="h-8" />
            <span className="text-sm text-brand-500 font-medium">for Hospitality</span>
          </div>
          <div className="flex items-center gap-6">
            <a href="/calculator" className="text-gray-400 hover:text-white transition">Cost Calculator</a>
            <a href="/login" className="bg-brand-600 hover:bg-brand-700 px-4 py-2 rounded-lg transition font-medium">Sign In</a>
          </div>
        </nav>
      </header>

      <main className="max-w-7xl mx-auto px-6">
        <section className="py-20 text-center">
          <p className="text-brand-500 font-medium mb-4">Built for hotels, restaurants, and food service</p>
          <h1 className="text-5xl md:text-6xl font-bold mb-6 leading-tight">
            No more clopening.<br />
            No more <span className="text-danger">unfair weekends.</span>
          </h1>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto mb-10">
            ShiftGuard keeps your FOH and BOH schedules compliant, fair, and fully staffed.
            Fair Workweek enforced. Split shifts tracked. Holiday rotation transparent.
          </p>
          <div className="flex gap-4 justify-center">
            <a href="/demo?industry=hospitality" className="bg-brand-600 hover:bg-brand-700 px-8 py-4 rounded-lg text-lg font-semibold transition">
              See Hospitality Demo
            </a>
            <a href="/calculator" className="border border-gray-600 hover:border-brand-500 px-8 py-4 rounded-lg text-lg transition">
              Calculate My Penalty Exposure
            </a>
          </div>
        </section>

        <section className="py-20 border-t border-gray-800">
          <h2 className="text-3xl font-bold text-center mb-12">FOH and BOH. Separate schedules. One platform.</h2>
          <div className="grid md:grid-cols-3 gap-8">
            <FeatureCard
              title="FOH Scheduling"
              description="Servers, bartenders, hosts — scheduled independently by floor manager. Covers, section assignments, side work rotation all tracked."
            />
            <FeatureCard
              title="BOH / Kitchen"
              description="Chef schedules the kitchen team separately. Line cooks, prep, dish — fair rotation of undesirable stations and closing shifts."
            />
            <FeatureCard
              title="Clopening Prevention"
              description="System blocks close-then-open shifts automatically. 10-11 hour rest enforced per jurisdiction. No more exhausted servers opening after closing."
            />
            <FeatureCard
              title="Holiday Fairness"
              description="Nobody works both Christmas AND New Year's. Priority auction lets staff rank holidays. Year-over-year memory ensures rotation."
            />
            <FeatureCard
              title="Minor Labor Compliance"
              description="Auto-blocks scheduling minors past 10pm. Tracks daily/weekly hour caps for under-18 workers. Zero chance of a DOL fine."
            />
            <FeatureCard
              title="Demand-Based Staffing"
              description="Reservation count up 30%? System recommends calling in extra servers. POS volume dropping? Offer VTO to save labor cost."
            />
          </div>
        </section>

        <section className="py-20 text-center border-t border-gray-800">
          <h2 className="text-4xl font-bold mb-4">Your restaurant. Your roles. Your rules.</h2>
          <p className="text-gray-400 text-lg mb-8">Define your own positions — Sommelier, Barback, Expo, whatever you call them. ShiftGuard adapts.</p>
          <a href="/demo?industry=hospitality" className="bg-brand-600 hover:bg-brand-700 px-10 py-5 rounded-lg text-xl font-semibold transition inline-block">
            Try Hospitality Demo (Free)
          </a>
        </section>
      </main>

      <footer className="border-t border-gray-800 py-8 text-center text-gray-500 text-sm">
        ShiftGuard for Hospitality &middot; Fair Workweek compliant &middot; AI-powered
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
