'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

export default function WorkerLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()

  return (
    <div className="min-h-screen bg-black text-white flex flex-col">
      {/* Header */}
      <header className="px-5 py-4 border-b border-white/[0.06] flex items-center justify-between sticky top-0 bg-black/90 backdrop-blur-xl z-10 safe-top">
        <Link href="/worker" className="flex items-center gap-2.5">
          <div className="w-8 h-8 bg-gradient-to-br from-brand-500 to-brand-700 rounded-lg flex items-center justify-center text-xs font-bold shadow-brand-glow">SG</div>
          <span className="font-semibold text-body">ShiftGuard</span>
        </Link>
        <Link href="/worker" className="p-2.5 text-gray-400 hover:text-white relative min-w-[48px] min-h-[48px] flex items-center justify-center">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
          </svg>
          <span className="absolute top-1.5 right-1.5 w-4.5 h-4.5 bg-red-500 rounded-full text-[10px] flex items-center justify-center font-bold text-white">4</span>
        </Link>
      </header>

      {/* Content */}
      <main className="flex-1 overflow-y-auto pb-nav">
        <div className="page-enter">
          {children}
        </div>
      </main>

      {/* Bottom Tab Bar */}
      <nav className="fixed bottom-0 left-0 right-0 bg-black/80 backdrop-blur-xl border-t border-white/[0.06] z-20">
        <div className="flex justify-around items-center px-4 pt-2 pb-safe" style={{height: '88px'}}>
          <NavItem href="/worker" label="Home" icon="home" active={pathname === '/worker'} />
          <NavItem href="/worker/schedule" label="Schedule" icon="calendar" active={pathname === '/worker/schedule'} />
          <NavItem href="/worker/request" label="Request" icon="plus" active={pathname === '/worker/request'} />
          <NavItem href="/worker/balance" label="Balance" icon="wallet" active={pathname === '/worker/balance'} />
        </div>
      </nav>
    </div>
  )
}

function NavItem({ href, label, icon, active }: { href: string, label: string, icon: string, active: boolean }) {
  const icons: Record<string, JSX.Element> = {
    home: <svg className="w-6 h-6" fill={active ? 'currentColor' : 'none'} stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={active ? 0 : 1.5} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" /></svg>,
    calendar: <svg className="w-6 h-6" fill={active ? 'currentColor' : 'none'} stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={active ? 0 : 1.5} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>,
    plus: <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={active ? 2.5 : 1.5} d="M12 4v16m8-8H4" /></svg>,
    wallet: <svg className="w-6 h-6" fill={active ? 'currentColor' : 'none'} stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={active ? 0 : 1.5} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" /></svg>,
  }

  return (
    <Link href={href} className={`flex flex-col items-center justify-center gap-1 min-w-[64px] min-h-[56px] relative rounded-xl transition-colors`}>
      {active && (
        <div className="absolute top-0.5 w-[56px] h-[32px] bg-brand-500/15 rounded-full" />
      )}
      <div className={`relative z-10 ${active ? 'text-brand-400' : 'text-gray-500'}`}>
        {icons[icon]}
      </div>
      <span className={`text-xs relative z-10 ${active ? 'text-brand-400 font-semibold' : 'text-gray-500 font-medium'}`}>{label}</span>
    </Link>
  )
}
