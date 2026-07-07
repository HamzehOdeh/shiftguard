export function CTASection({ headline, subtitle }: {
  headline?: string
  subtitle?: string
}) {
  return (
    <div className="bg-brand-950 border border-brand-800 rounded-2xl p-10 text-center">
      <h2 className="text-2xl font-bold mb-3 text-white">
        {headline || 'See ShiftGuard in action'}
      </h2>
      <p className="text-gray-400 mb-6 max-w-xl mx-auto">
        {subtitle || 'Upload your schedule and see violations in 60 seconds. No 6-month implementation.'}
      </p>
      <div className="flex flex-col sm:flex-row gap-3 justify-center">
        <a href="/demo" className="bg-brand-600 hover:bg-brand-700 px-8 py-3 rounded-lg font-medium transition text-white">
          Try Interactive Demo
        </a>
        <a href="/calculator" className="border border-gray-700 hover:border-gray-500 px-8 py-3 rounded-lg font-medium transition text-gray-300">
          Calculate My Risk
        </a>
      </div>
    </div>
  )
}
