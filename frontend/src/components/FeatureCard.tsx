export function FeatureCard({ icon, title, description }: {
  icon: string
  title: string
  description: string
}) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 hover:border-brand-600 transition group">
      <div className="text-3xl mb-3">{icon}</div>
      <h3 className="text-lg font-bold mb-2 group-hover:text-brand-400 transition">{title}</h3>
      <p className="text-gray-400 text-sm leading-relaxed">{description}</p>
    </div>
  )
}
