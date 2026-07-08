'use client'

import Link from 'next/link'
import { useState } from 'react'

export default function WorkerHome() {
  const [vetStatus, setVetStatus] = useState<'pending' | 'accepted' | 'declined'>('pending')

  function handleVetAccept() {
    setVetStatus('accepted')
  }
  function handleVetDecline() {
    setVetStatus('declined')
  }

  return (
    <div className="px-4 py-5 space-y-5">
      {/* Greeting */}
      <div>
        <h1 className="text-xl font-bold">Good morning, Sarah</h1>
        <p className="text-gray-400 text-sm">ED Nursing | Staff RN</p>
      </div>

      {/* Smart Notifications */}
      <div className="space-y-2">
        <NotificationCard
          icon="🌙"
          priority="high"
          title="Night shift in 24h — starts at 19:00"
          message="You're on night shift tomorrow 19:00-07:00. Tip: Nap for 90 minutes between 2-4 PM before your shift for peak alertness."
          actionLabel="View Schedule"
        />
        <NotificationCard
          icon="⏱️"
          priority="normal"
          title="Only 4h before overtime"
          message="At 36h this week, your next shift triggers OT pay (1.5x rate)."
        />
        <NotificationCard
          icon="💵"
          priority="high"
          title="VET Available: Thu Jul 10, 07:00-19:00"
          message="Premium pay shift covering for Maria. First to accept gets it!"
          actionLabel="Accept"
        />
        <NotificationCard
          icon="✅"
          priority="low"
          title="PTO Approved: Jul 15-17"
          message="Your time off was auto-approved. Coverage maintained. Enjoy!"
        />
      </div>

      {/* Today's Shift */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-gray-500 uppercase font-medium">Today</span>
          <span className="text-xs bg-green-900 text-green-400 px-2 py-0.5 rounded-full">On Shift</span>
        </div>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-lg font-bold">Day Shift</p>
            <p className="text-gray-400">07:00 - 19:00</p>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-400">Unit: ED</p>
            <p className="text-sm text-gray-400">Role: Staff RN</p>
          </div>
        </div>
      </div>

      {/* Hours Progress */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium">Hours this week</span>
          <span className="text-sm text-gray-400">36 / 40h</span>
        </div>
        <div className="w-full h-2 bg-gray-800 rounded-full overflow-hidden">
          <div className="h-full bg-brand-500 rounded-full" style={{width: '90%'}}></div>
        </div>
        <p className="text-xs text-gray-500 mt-2">4h remaining before overtime</p>
      </div>

      {/* VET Offer */}
      <div className="bg-brand-950 border border-brand-800 rounded-xl p-4 animate-slide-up">
        <div className="flex items-center gap-2 mb-3">
          <div className="w-2 h-2 bg-brand-500 rounded-full animate-pulse"></div>
          <span className="text-xs text-brand-400 uppercase font-medium">VET Available</span>
        </div>
        <p className="font-semibold">Thursday, Jul 10</p>
        <p className="text-gray-400 text-sm">07:00 - 19:00 | Covering for: Maria Rodriguez</p>
        <p className="text-gray-500 text-xs mt-1">Premium pay applies | Expires in 28 min</p>
        {vetStatus === 'pending' ? (
          <div className="flex gap-3 mt-4">
            <button onClick={handleVetAccept} className="flex-1 bg-brand-600 active:bg-brand-800 py-3 rounded-lg font-medium text-sm transition min-h-[48px]">
              Accept
            </button>
            <button onClick={handleVetDecline} className="flex-1 border border-gray-700 active:bg-gray-800 py-3 rounded-lg text-sm text-gray-300 transition min-h-[48px]">
              Decline
            </button>
          </div>
        ) : (
          <div className={`mt-4 p-3 rounded-lg text-sm font-medium text-center animate-slide-up ${
            vetStatus === 'accepted' ? 'bg-green-900/50 text-green-400' : 'bg-gray-800 text-gray-400'
          }`}>
            {vetStatus === 'accepted' ? 'Accepted! Confirmation sent.' : 'Declined. Offered to next worker.'}
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-2 gap-3">
        <Link href="/worker/request" className="bg-gray-900 border border-gray-800 rounded-xl p-4 text-left active:bg-gray-800 transition block min-h-[88px]">
          <span className="text-2xl mb-1 block">🤒</span>
          <span className="text-sm font-medium">Report Sick</span>
          <span className="text-xs text-gray-500 block">One-tap callout</span>
        </Link>
        <Link href="/worker/schedule" className="bg-gray-900 border border-gray-800 rounded-xl p-4 text-left active:bg-gray-800 transition block min-h-[88px]">
          <span className="text-2xl mb-1 block">🔄</span>
          <span className="text-sm font-medium">Swap Shift</span>
          <span className="text-xs text-gray-500 block">Propose a trade</span>
        </Link>
        <Link href="/worker/schedule" className="bg-gray-900 border border-gray-800 rounded-xl p-4 text-left active:bg-gray-800 transition block min-h-[88px]">
          <span className="text-2xl mb-1 block">👥</span>
          <span className="text-sm font-medium">On Floor Now</span>
          <span className="text-xs text-gray-500 block">Who's working</span>
        </Link>
        <Link href="/worker/balance" className="bg-gray-900 border border-gray-800 rounded-xl p-4 text-left active:bg-gray-800 transition block min-h-[88px]">
          <span className="text-2xl mb-1 block">💬</span>
          <span className="text-sm font-medium">Ask AI</span>
          <span className="text-xs text-gray-500 block">Hours, balance, etc.</span>
        </Link>
      </div>

      {/* Balance Summary */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
        <h3 className="text-sm font-medium mb-3">My Balances</h3>
        <div className="grid grid-cols-3 gap-3 text-center">
          <div>
            <p className="text-lg font-bold text-white">48h</p>
            <p className="text-[10px] text-gray-500">PTO</p>
          </div>
          <div>
            <p className="text-lg font-bold text-white">16h</p>
            <p className="text-[10px] text-gray-500">Sick</p>
          </div>
          <div>
            <p className="text-lg font-bold text-green-400">20h</p>
            <p className="text-[10px] text-gray-500">UPT</p>
          </div>
        </div>
      </div>

      {/* Upcoming */}
      <div>
        <h3 className="text-sm font-medium mb-3">This Week</h3>
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
    <div className={`bg-gray-900 border border-gray-800 border-l-4 ${borderColor} rounded-lg p-3`}>
      <div className="flex items-start gap-2">
        <span className="text-lg flex-shrink-0">{icon}</span>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium leading-tight">{title}</p>
          <p className="text-xs text-gray-400 mt-1 leading-relaxed">{message}</p>
          {actionLabel && (
            <Link href={actionLabel === 'View Schedule' ? '/worker/schedule' : '/worker'} className="mt-2 inline-block text-xs bg-brand-600 active:bg-brand-800 px-4 py-2 rounded-md font-medium transition min-h-[36px] leading-relaxed">
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
    <div className={`flex items-center justify-between px-3 py-2.5 rounded-lg ${
      active ? 'bg-brand-950 border border-brand-800' : off ? 'bg-gray-900/50' : 'bg-gray-900'
    }`}>
      <div className="flex items-center gap-3">
        <div className="text-center w-10">
          <p className="text-xs text-gray-500">{day}</p>
          <p className="text-sm font-medium">{date.split(' ')[1]}</p>
        </div>
        <div>
          <p className={`text-sm ${off ? 'text-gray-500' : 'font-medium'}`}>{time}</p>
        </div>
      </div>
      <span className={`text-xs px-2 py-0.5 rounded-full ${
        type === 'Night' ? 'bg-purple-900 text-purple-400' :
        type === 'Off' ? 'bg-gray-800 text-gray-500' :
        'bg-blue-900 text-blue-400'
      }`}>{type}</span>
    </div>
  )
}
