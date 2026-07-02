import './globals.css'

export const metadata = {
  title: 'ShiftGuard - AI-Powered Workforce Compliance',
  description: 'Schedule with confidence. Never pay another compliance fine.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-gray-950 text-white min-h-screen">{children}</body>
    </html>
  )
}
