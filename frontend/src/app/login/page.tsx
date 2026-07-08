'use client'

import { useState } from 'react'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [tenant, setTenant] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError('')

    const DEMO_USERS: Record<string, { role: string; name: string; redirect: string }> = {
      'manager@metro-general.com': { role: 'manager', name: 'Dr. Rachel Torres', redirect: '/reporting' },
      'sarah.chen@metro-general.com': { role: 'worker', name: 'Sarah Chen', redirect: '/worker' },
      'hr@metro-general.com': { role: 'admin', name: 'Admin User', redirect: '/reporting' },
    }

    await new Promise(resolve => setTimeout(resolve, 800))

    const demoUser = DEMO_USERS[email]
    if (demoUser && password === 'demo123') {
      localStorage.setItem('token', 'demo_token_' + demoUser.role)
      localStorage.setItem('user', JSON.stringify({ email, role: demoUser.role, name: demoUser.name, tenant }))
      window.location.href = demoUser.redirect
    } else {
      setError('Invalid credentials. Use demo credentials shown below.')
    }

    setLoading(false)
  }

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center px-4">
      <div className="w-full max-w-md space-y-8">
        {/* Logo */}
        <div className="text-center">
          <div className="w-12 h-12 bg-brand-500 rounded-xl flex items-center justify-center text-xl font-bold mx-auto mb-4">SG</div>
          <h1 className="text-2xl font-bold text-white">Sign in to ShiftGuard</h1>
          <p className="text-gray-400 text-sm mt-2">Schedule with confidence. Never pay another compliance fine.</p>
        </div>

        {/* Login form */}
        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="text-xs text-gray-500 font-medium uppercase block mb-1">Organization</label>
            <select
              value={tenant}
              onChange={(e) => setTenant(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-white focus:border-brand-500 focus:outline-none"
            >
              <option value="">Select your organization...</option>
              <option value="metro-general">Metro General Hospital</option>
              <option value="acme-warehouse">ACME Fulfillment Center</option>
              <option value="coastal-retail">Coastal Retail Group</option>
              <option value="summit-hospitality">Summit Hospitality</option>
              <option value="precision-mfg">Precision Manufacturing</option>
            </select>
          </div>

          <div>
            <label className="text-xs text-gray-500 font-medium uppercase block mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@company.com"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder:text-gray-600 focus:border-brand-500 focus:outline-none"
              required
            />
          </div>

          <div>
            <label className="text-xs text-gray-500 font-medium uppercase block mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder:text-gray-600 focus:border-brand-500 focus:outline-none"
              required
            />
          </div>

          {error && (
            <div className="bg-red-950 border border-red-800 rounded-lg p-3 text-sm text-red-400">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-brand-600 hover:bg-brand-700 disabled:bg-gray-700 disabled:text-gray-500 py-3 rounded-lg font-medium transition text-white"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        {/* Demo access */}
        <div className="border-t border-gray-800 pt-6 text-center space-y-3">
          <p className="text-gray-500 text-sm">No account? Try the demo:</p>
          <a
            href="/demo"
            className="block w-full border border-brand-600 text-brand-400 hover:bg-brand-950 py-3 rounded-lg font-medium transition text-center"
          >
            Launch Interactive Demo
          </a>
          <a
            href="/calculator"
            className="block w-full border border-gray-700 text-gray-400 hover:border-gray-500 py-3 rounded-lg text-sm transition text-center"
          >
            Free Compliance Risk Calculator
          </a>
        </div>

        {/* Role hints */}
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 text-xs text-gray-500">
          <p className="font-medium text-gray-400 mb-2">Demo Credentials:</p>
          <p>Manager: manager@metro-general.com / demo123</p>
          <p>Worker: sarah.chen@metro-general.com / demo123</p>
          <p>HR Admin: hr@metro-general.com / demo123</p>
        </div>
      </div>
    </div>
  )
}
