'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

const TABS = [
  { href: '/healthcare/app', label: 'Home', icon: '🏥' },
  { href: '/healthcare/app/otto', label: 'Otto', icon: '🤖' },
  { href: '/healthcare/app/residency', label: 'Residency', icon: '🩺' },
  { href: '/healthcare/app/nursing', label: 'Nursing', icon: '👩‍⚕️' },
  { href: '/healthcare/app/admin', label: 'Admin', icon: '📋' },
]

export default function HealthcareAppLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()

  return (
    <div className="min-h-screen bg-surface-base text-white flex flex-col">
      {/* Top header */}
      <header className="safe-top border-b border-white/[0.06] bg-surface-raised px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-gradient-to-br from-brand-500 to-brand-700 rounded-lg flex items-center justify-center text-sm font-bold">SG</div>
          <div>
            <h1 className="text-body-sm font-bold">ShiftGuard <span className="text-brand-400">Healthcare</span></h1>
            <p className="text-[11px] text-gray-400">Program Director View</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="bg-green-500/15 text-green-400 text-[11px] font-medium px-2.5 py-1 rounded-full">ACGME Compliant</span>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto pb-nav">
        {children}
      </main>

      {/* Bottom navigation */}
      <nav className="fixed bottom-0 left-0 right-0 bg-surface-raised border-t border-white/[0.06] pb-safe z-50">
        <div className="flex items-center justify-around h-16">
          {TABS.map(tab => {
            const isActive = pathname === tab.href || (tab.href !== '/healthcare/app' && pathname?.startsWith(tab.href))
            return (
              <Link
                key={tab.href}
                href={tab.href}
                className={`flex flex-col items-center gap-0.5 min-w-[56px] py-2 rounded-xl transition ${
                  isActive ? 'text-brand-400' : 'text-gray-500'
                }`}
              >
                <span className="text-xl">{tab.icon}</span>
                <span className="text-[10px] font-medium">{tab.label}</span>
              </Link>
            )
          })}
        </div>
      </nav>
    </div>
  )
}
