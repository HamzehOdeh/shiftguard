import './globals.css'
import type { Viewport, Metadata } from 'next'
import { ServiceWorkerRegister } from './sw-register'

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  viewportFit: 'cover',
  themeColor: '#030712',
}

export const metadata: Metadata = {
  title: 'ShiftGuard - AI-Powered Workforce Compliance',
  description: 'Schedule with confidence. Never pay another compliance fine.',
  manifest: '/manifest.json',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'black-translucent',
    title: 'ShiftGuard',
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="apple-touch-icon" href="/icon-192.png" />
      </head>
      <body className="bg-black text-white min-h-screen overscroll-none">
        <ServiceWorkerRegister />
        {children}
      </body>
    </html>
  )
}
