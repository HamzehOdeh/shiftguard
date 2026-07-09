'use client'

import { useState } from 'react'

type DayStatus = 'shift' | 'off' | 'pto_approved' | 'pto_pending' | 'blackout' | 'limited' | 'open'

interface CalendarDay {
  date: number
  status: DayStatus
  shiftCode?: string
  teammatesOff?: number
  spotsRemaining?: number
}

const DAYS_OF_WEEK = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December']

function generateDemoMonth(year: number, month: number): CalendarDay[] {
  const daysInMonth = new Date(year, month + 1, 0).getDate()
  const days: CalendarDay[] = []

  for (let d = 1; d <= daysInMonth; d++) {
    const date = new Date(year, month, d)
    const jsDay = date.getDay()
    const isWorkDay = [0, 1, 2, 3].includes(jsDay)

    let status: DayStatus = isWorkDay ? 'shift' : 'off'
    let teammatesOff = 0
    let spotsRemaining = isWorkDay ? 3 : 5

    if (d >= 15 && d <= 17) {
      status = 'pto_approved'
      spotsRemaining = 2
    }

    if (d === 22) {
      status = 'pto_pending'
    }

    if (d === 4 && month === 6) {
      status = 'blackout'
      spotsRemaining = 0
    }

    if (d === 25) {
      spotsRemaining = 1
      if (status === 'shift') status = 'limited'
      teammatesOff = 2
    }

    if (d % 7 === 0 || d % 11 === 0) {
      teammatesOff = Math.min(2, teammatesOff + 1)
    }

    days.push({
      date: d,
      status,
      shiftCode: isWorkDay ? 'DA5' : undefined,
      teammatesOff,
      spotsRemaining,
    })
  }
  return days
}

function getFirstDayOffset(year: number, month: number): number {
  const day = new Date(year, month, 1).getDay()
  return day === 0 ? 6 : day - 1
}

function getStatusColor(status: DayStatus): string {
  switch (status) {
    case 'shift': return 'bg-purple-500/15 border-purple-500/30'
    case 'off': return 'bg-surface-highlight/50 border-white/[0.06]'
    case 'pto_approved': return 'bg-cyan-500/15 border-cyan-500/30'
    case 'pto_pending': return 'bg-cyan-500/10 border-yellow-500/40 border-dashed'
    case 'blackout': return 'bg-red-500/15 border-red-500/30'
    case 'limited': return 'bg-yellow-500/15 border-yellow-500/30'
    case 'open': return 'bg-green-500/15 border-green-500/30'
    default: return 'bg-surface-highlight/50 border-white/[0.06]'
  }
}

function getStatusLabel(status: DayStatus): string {
  switch (status) {
    case 'shift': return 'On'
    case 'off': return 'Off'
    case 'pto_approved': return 'PTO'
    case 'pto_pending': return 'Pend'
    case 'blackout': return 'Blk'
    case 'limited': return 'Ltd'
    case 'open': return 'Open'
    default: return ''
  }
}

export default function WorkerSchedulePage() {
  const today = new Date()
  const [monthOffset, setMonthOffset] = useState(0)
  const [selectedDay, setSelectedDay] = useState<CalendarDay | null>(null)
  const [showRequestForm, setShowRequestForm] = useState(false)
  const [requestConfirmed, setRequestConfirmed] = useState(false)

  const viewDate = new Date(today.getFullYear(), today.getMonth() + monthOffset, 1)
  const viewYear = viewDate.getFullYear()
  const viewMonth = viewDate.getMonth()

  const days = generateDemoMonth(viewYear, viewMonth)
  const firstDayOffset = getFirstDayOffset(viewYear, viewMonth)

  return (
    <div className="px-5 py-6 space-y-6">
      {/* Confirmation toast */}
      {requestConfirmed && (
        <div className="fixed top-16 left-1/2 -translate-x-1/2 z-50 bg-green-500/10 border border-green-500/20 text-green-400 px-5 py-3.5 rounded-2xl shadow-elevation-2 text-body-sm font-medium animate-pulse backdrop-blur-sm">
          Request submitted — auto-approved!
        </div>
      )}

      {/* Balance bar */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-surface-raised border border-white/[0.06] rounded-2xl p-3.5 text-center shadow-elevation-1">
          <p className="text-heading-sm font-bold">6d</p>
          <p className="text-xs text-gray-500 mt-0.5">PTO Left</p>
        </div>
        <div className="bg-surface-raised border border-white/[0.06] rounded-2xl p-3.5 text-center shadow-elevation-1">
          <p className="text-heading-sm font-bold">2d</p>
          <p className="text-xs text-gray-500 mt-0.5">Sick Left</p>
        </div>
        <div className="bg-surface-raised border border-white/[0.06] rounded-2xl p-3.5 text-center shadow-elevation-1">
          <p className="text-heading-sm font-bold text-green-400">20h</p>
          <p className="text-xs text-gray-500 mt-0.5">UPT Left</p>
        </div>
      </div>

      {/* Month navigation */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => setMonthOffset(monthOffset - 1)}
          className="min-w-[44px] min-h-[44px] flex items-center justify-center text-gray-400 hover:text-white active:scale-95 transition rounded-xl"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <h2 className="text-heading-sm font-bold">{MONTHS[viewMonth]} {viewYear}</h2>
        <button
          onClick={() => setMonthOffset(monthOffset + 1)}
          className="min-w-[44px] min-h-[44px] flex items-center justify-center text-gray-400 hover:text-white active:scale-95 transition rounded-xl"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-3 text-xs text-gray-400">
        <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-md bg-purple-500/15 border border-purple-500/30"></span>Shift</span>
        <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-md bg-surface-highlight/50 border border-white/[0.06]"></span>Off</span>
        <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-md bg-cyan-500/15 border border-cyan-500/30"></span>PTO</span>
        <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-md bg-yellow-500/15 border border-yellow-500/30"></span>Limited</span>
        <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-md bg-red-500/15 border border-red-500/30"></span>Blackout</span>
      </div>

      {/* Calendar grid */}
      <div className="bg-surface-raised border border-white/[0.06] rounded-2xl p-3 shadow-elevation-1">
        {/* Day headers */}
        <div className="grid grid-cols-7 gap-1 mb-1">
          {DAYS_OF_WEEK.map(day => (
            <div key={day} className="text-center text-[11px] text-gray-500 font-medium py-1">
              {day}
            </div>
          ))}
        </div>

        {/* Day cells */}
        <div className="grid grid-cols-7 gap-1">
          {Array.from({ length: firstDayOffset }).map((_, i) => (
            <div key={`empty-${i}`} className="min-h-[44px]" />
          ))}

          {days.map((day) => {
            const isToday = day.date === today.getDate() && viewMonth === today.getMonth() && viewYear === today.getFullYear()

            return (
              <button
                key={day.date}
                onClick={() => { setSelectedDay(day); setShowRequestForm(false) }}
                className={`min-h-[44px] rounded-lg border flex flex-col items-center justify-center relative transition press-scale
                  ${getStatusColor(day.status)}
                  ${isToday ? 'ring-2 ring-white ring-offset-1 ring-offset-surface-base' : ''}
                  ${selectedDay?.date === day.date ? 'ring-2 ring-brand-500 ring-offset-1 ring-offset-surface-base' : ''}
                `}
              >
                <span className="text-sm font-bold">{day.date}</span>
                <span className="text-[10px] text-gray-400">{getStatusLabel(day.status)}</span>
                {day.teammatesOff && day.teammatesOff > 0 && (
                  <span className="absolute -top-1 -right-1 w-4 h-4 bg-yellow-500/20 border border-yellow-500/30 rounded-full text-[9px] flex items-center justify-center font-bold text-yellow-400">
                    {day.teammatesOff}
                  </span>
                )}
              </button>
            )
          })}
        </div>
      </div>

      {/* Selected day detail */}
      {selectedDay && (
        <div className="bg-surface-raised border border-white/[0.06] border-t-2 border-t-brand-500 rounded-2xl p-5 space-y-4 shadow-elevation-2">
          <div className="flex items-center justify-between">
            <h3 className="text-body font-bold">
              {MONTHS[viewMonth]} {selectedDay.date}, {viewYear}
            </h3>
            <span className={`text-xs px-3 py-1 rounded-full font-medium ${
              selectedDay.status === 'shift' ? 'bg-purple-500/15 text-purple-400' :
              selectedDay.status === 'pto_approved' ? 'bg-cyan-500/15 text-cyan-400' :
              selectedDay.status === 'blackout' ? 'bg-red-500/15 text-red-400' :
              selectedDay.status === 'limited' ? 'bg-yellow-500/15 text-yellow-400' :
              selectedDay.status === 'pto_pending' ? 'bg-yellow-500/15 text-yellow-400' :
              'bg-surface-highlight text-gray-400'
            }`}>
              {selectedDay.status === 'shift' ? `Shift: ${selectedDay.shiftCode}` :
               selectedDay.status === 'pto_approved' ? 'PTO Approved' :
               selectedDay.status === 'pto_pending' ? 'PTO Pending' :
               selectedDay.status === 'blackout' ? 'Blackout' :
               selectedDay.status === 'limited' ? 'Limited Coverage' :
               'Day Off'}
            </span>
          </div>

          {selectedDay.status === 'shift' && (
            <div className="text-body-sm text-gray-400 space-y-1">
              <p>Shift: Day 12h | 07:00 - 19:00</p>
              <p>Unit: ED | Role: Staff RN</p>
            </div>
          )}

          <div className="flex items-center justify-between text-body-sm">
            <span className="text-gray-400">Team coverage:</span>
            <span className={`font-semibold ${
              (selectedDay.spotsRemaining ?? 0) > 2 ? 'text-green-400' :
              (selectedDay.spotsRemaining ?? 0) > 0 ? 'text-yellow-400' :
              'text-red-400'
            }`}>
              {selectedDay.spotsRemaining} spots available
            </span>
          </div>

          {selectedDay.teammatesOff && selectedDay.teammatesOff > 0 && (
            <div className="text-body-sm text-gray-400">
              <span className="text-yellow-400 font-medium">{selectedDay.teammatesOff} teammate(s)</span> off this day
            </div>
          )}

          {/* Request PTO button */}
          {selectedDay.status !== 'blackout' && selectedDay.status !== 'pto_approved' && selectedDay.status !== 'pto_pending' && (
            <button
              onClick={() => setShowRequestForm(true)}
              className="w-full btn-primary py-3.5 text-body-sm"
            >
              Request Time Off
            </button>
          )}

          {selectedDay.status === 'blackout' && (
            <p className="text-xs text-red-400">This date is blocked — no time off requests accepted.</p>
          )}
        </div>
      )}

      {/* PTO Request form */}
      {showRequestForm && selectedDay && (
        <div className="bg-surface-raised border border-brand-500/20 rounded-2xl p-5 space-y-4 shadow-elevation-2">
          <h3 className="text-body font-bold text-brand-400">Request Time Off</h3>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-gray-500 block mb-1.5 font-medium">Start Date</label>
              <div className="bg-surface-overlay border border-white/[0.06] rounded-xl px-3.5 py-3 text-body-sm">
                {MONTHS[viewMonth]} {selectedDay.date}
              </div>
            </div>
            <div>
              <label className="text-xs text-gray-500 block mb-1.5 font-medium">End Date</label>
              <div className="bg-surface-overlay border border-white/[0.06] rounded-xl px-3.5 py-3 text-body-sm">
                {MONTHS[viewMonth]} {selectedDay.date}
              </div>
            </div>
          </div>

          <div>
            <label className="text-xs text-gray-500 block mb-1.5 font-medium">Priority</label>
            <select className="w-full bg-surface-overlay border border-white/[0.06] rounded-xl px-3.5 py-3 text-body-sm text-white">
              <option value="1">Priority 1 (Most important)</option>
              <option value="2">Priority 2</option>
              <option value="3">Priority 3</option>
            </select>
          </div>

          <div>
            <label className="text-xs text-gray-500 block mb-1.5 font-medium">Reason (optional)</label>
            <input
              type="text"
              placeholder="e.g., Family event, appointment"
              className="w-full bg-surface-overlay border border-white/[0.06] rounded-xl px-3.5 py-3 text-body-sm text-white placeholder:text-gray-600"
            />
          </div>

          {/* Coverage check result */}
          <div className={`rounded-2xl p-4 text-body-sm ${
            (selectedDay.spotsRemaining ?? 0) > 1 ? 'bg-green-500/10 border border-green-500/20' :
            (selectedDay.spotsRemaining ?? 0) > 0 ? 'bg-yellow-500/10 border border-yellow-500/20' :
            'bg-red-500/10 border border-red-500/20'
          }`}>
            <p className="font-semibold mb-1">
              {(selectedDay.spotsRemaining ?? 0) > 1 ? 'Likely auto-approved' :
               (selectedDay.spotsRemaining ?? 0) > 0 ? 'May need manager review' :
               'Low chance of approval'}
            </p>
            <p className="text-xs text-gray-400">
              {selectedDay.spotsRemaining} coverage spot(s) remaining.
              {selectedDay.teammatesOff ? ` ${selectedDay.teammatesOff} teammate(s) already off.` : ''}
            </p>
          </div>

          <div className="flex gap-3">
            <button
              onClick={() => {
                setShowRequestForm(false)
                setRequestConfirmed(true)
                setTimeout(() => setRequestConfirmed(false), 3000)
              }}
              className="flex-1 btn-primary py-3.5 text-body-sm"
            >
              Submit Request
            </button>
            <button
              onClick={() => setShowRequestForm(false)}
              className="flex-1 border border-white/[0.1] active:bg-surface-highlight py-3.5 rounded-2xl text-body-sm text-gray-300 transition press-scale"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Coverage heatmap summary */}
      <div className="bg-surface-raised border border-white/[0.06] rounded-2xl p-5 shadow-elevation-1">
        <h3 className="text-body-sm font-medium mb-4">Coverage This Month</h3>
        <div className="space-y-3">
          <div className="flex items-center justify-between text-body-sm">
            <span className="text-gray-400">Best days to request off:</span>
            <span className="text-green-400 font-semibold">Tue, Wed, Thu</span>
          </div>
          <div className="flex items-center justify-between text-body-sm">
            <span className="text-gray-400">Avoid requesting:</span>
            <span className="text-red-400 font-semibold">Jul 4, Jul 25</span>
          </div>
          <div className="flex items-center justify-between text-body-sm">
            <span className="text-gray-400">Team size (DA5):</span>
            <span className="text-white font-medium">8 associates</span>
          </div>
          <div className="flex items-center justify-between text-body-sm">
            <span className="text-gray-400">Min staffing:</span>
            <span className="text-white font-medium">5 required</span>
          </div>
        </div>
      </div>
    </div>
  )
}
