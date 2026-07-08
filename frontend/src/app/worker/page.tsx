'use client'

import Link from 'next/link'
import { useState } from 'react'

export default function WorkerHome() {
  const [vetStatus, setVetStatus] = useState<'pending' | 'accepted' | 'declined'>('pending')

  return (
    <div className="px-5 py-6 space-y-6">
      {/* Greeting */}
      <div>
        <h1 className="text-heading-md font-bold">Good morning, Sarah</h1>
        <p className="text-gray-400 text-body-sm mt-1">ED Nursing | Staff RN</p>
      </div>

      {/* Smart Notifications */}
      <div className="space-y-3">
        <NotificationCard
          icon="🌙"
          priority="high"
          title="Night shift in 24h — starts at 19:00"
          message="Tip: Nap for 90 minutes between 2-4 PM before your shift for peak alertness."
          actionLabel="View Schedule"
        />
        <NotificationCard
          icon="⏱️"
          priority="normal"
          title="Only 4h before overtime"
          message="At 36h this week. Next shift triggers OT pay (1.5x rate)."
        />
        <NotificationCard
          icon="✅"
          priority="low"
          title="PTO Approved: Jul 15-17"
          message="Auto-approved. Coverage maintained. Enjoy!"
        />
      </div>

      {/* Today's Shift — Hero Card */}
      <div className="bg-surface-raised border border-white/[0.06] border-t-2 border-t-green-500 rounded-2xl p-5 shadow-elevation-2">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs text-gray-500 uppercase font-medium tracking-wide">Today</span>
          <span className="text-xs bg-green-500/20 text-green-400 px-3 py-1 rounded-full font-medium">On Shift</span>
        </div>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-heading-sm font-bold">Day Shift</p>
            <p className="text-gray-400 text-body-sm">07:00 - 19:00</p>
          </div>
          <div className="text-right">
            <p className="text-body-sm text-gray-400">Unit: ED</p>
            <p className="text-body-sm text-gray-400">Role: Staff RN</p>
          </div>
        </div>
      </div>

      {/* Hours Progress */}
      <div className="bg-surface-raised border border-white/[0.06] rounded-2xl p-5 shadow-elevation-1">
        <div className="flex justify-between items-center mb-3">
          <span className="text-body-sm font-medium">Hours this week</span>
          <span className="text-body-sm text-gray-400">36 / 40h</span>
        </div>
        <div className="w-full h-2.5 bg-surface-highlight rounded-full overflow-hidden shadow-inner-soft">
          <div className="h-full bg-brand-500 rounded-full relative" style={{width: '90%'}}>
            <div className="absolute inset-0 progress-shimmer rounded-full"></div>
          </div>
        </div>
        <p className="text-xs text-gray-500 mt-2">4h remaining before overtime</p>
      </div>

      {/* VET Offer — Brand Card */}
      <div className="bg-gradient-to-br from-brand-950/80 to-brand-900/60 border border-brand-500/20 rounded-2xl p-5 shadow-brand-glow">
        <div className="flex items-center gap-2 mb-3">
          <div className="w-2 h-2 bg-brand-400 rounded-full animate-pulse"></div>
          <span className="text-xs text-brand-400 uppercase font-medium tracking-wide">VET Available</span>
        </div>
        <p className="font-semibold text-body">Thursday, Jul 10</p>
        <p className="text-gray-400 text-body-sm">07:00 - 19:00 | Covering for: Maria Rodriguez</p>
        <p className="text-gray-500 text-xs mt-1">Premium pay applies | Expires in 28 min</p>
        {vetStatus === 'pending' ? (
          <div className="flex gap-3 mt-4">
            <button onClick={() => setVetStatus('accepted')} className="flex-1 btn-primary py-3.5 text-body-sm">
              Accept
            </button>
            <button onClick={() => setVetStatus('declined')} className="flex-1 border border-white/[0.1] active:bg-surface-highlight py-3.5 rounded-2xl text-body-sm text-gray-300 transition press-scale">
              Decline
            </button>
          </div>
        ) : (
          <div className={`mt-4 p-4 rounded-xl text-body-sm font-medium text-center ${
            vetStatus === 'accepted' ? 'bg-green-500/10 text-green-400 border border-green-500/20' : 'bg-surface-highlight text-gray-400'
          }`}>
            {vetStatus === 'accepted' ? 'Accepted! Confirmation sent.' : 'Declined. Offered to next worker.'}
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-2 gap-3">
        <Link href="/worker/request" className="bg-surface-raised border border-white/[0.06] rounded-2xl p-5 text-left shadow-elevation-1 press-card block">
          <span className="text-3xl mb-2 block">🤒</span>
          <span className="text-body-sm font-medium block">Report Sick</span>
          <span className="text-xs text-gray-500 block mt-0.5">One-tap callout</span>
        </Link>
        <Link href="/worker/schedule" className="bg-surface-raised border border-white/[0.06] rounded-2xl p-5 text-left shadow-elevation-1 press-card block">
          <span className="text-3xl mb-2 block">🔄</span>
          <span className="text-body-sm font-medium block">Swap Shift</span>
          <span className="text-xs text-gray-500 block mt-0.5">Propose a trade</span>
        </Link>
        <Link href="/worker/schedule" className="bg-surface-raised border border-white/[0.06] rounded-2xl p-5 text-left shadow-elevation-1 press-card block">
          <span className="text-3xl mb-2 block">👥</span>
          <span className="text-body-sm font-medium block">On Floor Now</span>
          <span className="text-xs text-gray-500 block mt-0.5">Who's working</span>
        </Link>
        <Link href="/worker/balance" className="bg-surface-raised border border-white/[0.06] rounded-2xl p-5 text-left shadow-elevation-1 press-card block">
          <span className="text-3xl mb-2 block">💬</span>
          <span className="text-body-sm font-medium block">Ask AI</span>
          <span className="text-xs text-gray-500 block mt-0.5">Hours, balance, etc.</span>
        </Link>
      </div>

      {/* Balance Summary */}
      <div className="bg-surface-raised border border-white/[0.06] rounded-2xl p-5 shadow-elevation-1">
        <h3 className="text-body-sm font-medium mb-4">My Balances</h3>
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-heading-sm font-bold text-white">48h</p>
            <p className="text-xs text-gray-500 mt-1">PTO</p>
          </div>
          <div>
            <p className="text-heading-sm font-bold text-white">16h</p>
            <p className="text-xs text-gray-500 mt-1">Sick</p>
          </div>
          <div>
            <p className="text-heading-sm font-bold text-green-400">20h</p>
            <p className="text-xs text-gray-500 mt-1">UPT</p>
          </div>
        </div>
      </div>

      {/* This Week */}
      <div>
        <h3 className="text-body-sm font-medium mb-3">This Week</h3>
        <div className="space-y-2">
          <ShiftRow day="Mon" date="Jul 7" time="07:00-19:00" type="Day" active />
          <ShiftRow day="Tue" date="Jul 8" time="07:00-19:00" type="Day" />
          <ShiftRow day="Wed" date="Jul 9" time="07:00-19:00" type="Day" />
          <ShiftRow day="Thu" date="Jul 10" time="Off" type="Off" off />
          <ShiftRow day="Fri" date="Jul 11" time="19:00-07:00" type="Night" />
        </div>
      </div>
    </div>
  )
}

function NotificationCard({ icon, priority, title, message, actionLabel }: {
  icon: string, priority: 'urgent' | 'high' | 'normal' | 'low',
  title: string, message: string, actionLabel?: string
}) {
  const borderColor = {
    urgent: 'border-l-red-500',
    high: 'border-l-orange-500',
    normal: 'border-l-brand-500',
    low: 'border-l-gray-600',
  }[priority]

  return (
    <div className={`bg-surface-raised border border-white/[0.06] border-l-4 ${borderColor} rounded-2xl p-4 shadow-elevation-1`}>
      <div className="flex items-start gap-3">
        <span className="text-xl flex-shrink-0">{icon}</span>
        <div className="flex-1 min-w-0">
          <p className="text-body-sm font-medium leading-tight">{title}</p>
          <p className="text-xs text-gray-400 mt-1.5 leading-relaxed">{message}</p>
          {actionLabel && (
            <Link href={actionLabel === 'View Schedule' ? '/worker/schedule' : '/worker'} className="mt-3 inline-block text-xs btn-primary py-2 px-4 rounded-xl shadow-none text-center">
              {actionLabel}
            </Link>
          )}
        </div>
      </div>
    </div>
  )
}

function ShiftRow({ day, date, time, type, active, off }: {
  day: string, date: string, time: string, type: string, active?: boolean, off?: boolean
}) {
  return (
    <div className={`flex items-center justify-between px-4 py-3.5 rounded-xl ${
      active ? 'bg-surface-overlay border border-brand-500/20 shadow-elevation-1' : off ? 'bg-surface-raised/50' : 'bg-surface-raised border border-white/[0.04]'
    }`}>
      <div className="flex items-center gap-4">
        <div className="text-center w-10">
          <p className="text-xs text-gray-500">{day}</p>
          <p className="text-body-sm font-medium">{date.split(' ')[1]}</p>
        </div>
        <div>
          <p className={`text-body-sm ${off ? 'text-gray-500' : 'font-medium'}`}>{time}</p>
        </div>
      </div>
      <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${
        type === 'Night' ? 'bg-purple-500/15 text-purple-400' :
        type === 'Off' ? 'bg-surface-highlight text-gray-500' :
        'bg-blue-500/15 text-blue-400'
      }`}>{type}</span>
    </div>
  )
}
