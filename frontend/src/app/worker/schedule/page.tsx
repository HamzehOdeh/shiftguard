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

  // Demo: DA5 shift pattern (Sun-Wed on, Thu-Sat off)
  const workDays = [0, 1, 2, 3] // Mon, Tue, Wed, Thu (JS: 0=Mon in our grid)
  // Actual JS getDay: 0=Sun, 1=Mon... we'll map accordingly
  for (let d = 1; d <= daysInMonth; d++) {
    const date = new Date(year, month, d)
    const jsDay = date.getDay() // 0=Sun, 1=Mon...
    const isWorkDay = [0, 1, 2, 3].includes(jsDay) // Sun-Wed

    let status: DayStatus = isWorkDay ? 'shift' : 'off'
    let teammatesOff = 0
    let spotsRemaining = isWorkDay ? 3 : 5

    // Demo PTO: 15th-17th approved
    if (d >= 15 && d <= 17) {
      status = 'pto_approved'
      spotsRemaining = 2
    }

    // Demo: 22nd pending
    if (d === 22) {
      status = 'pto_pending'
    }

    // Demo: blackout on 4th (holiday)
    if (d === 4 && month === 6) { // July 4th
      status = 'blackout'
      spotsRemaining = 0
    }

    // Demo: limited on 25th
    if (d === 25) {
      spotsRemaining = 1
      if (status === 'shift') status = 'limited'
      teammatesOff = 2
    }

    // Random teammates off
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
  // Convert: JS 0=Sun → grid 6, JS 1=Mon → grid 0
  return day === 0 ? 6 : day - 1
}

function getStatusColor(status: DayStatus): string {
  switch (status) {
    case 'shift': return 'bg-purple-900 border-purple-700'
    case 'off': return 'bg-gray-800 border-gray-700'
    case 'pto_approved': return 'bg-cyan-900 border-cyan-600'
    case 'pto_pending': return 'bg-cyan-900/50 border-yellow-500 border-dashed'
    case 'blackout': return 'bg-red-900 border-red-600'
    case 'limited': return 'bg-yellow-900 border-yellow-600'
    case 'open': return 'bg-green-900 border-green-600'
    default: return 'bg-gray-800 border-gray-700'
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
    <div className="px-4 py-5 space-y-4">
      {/* Confirmation toast */}
      {requestConfirmed && (
        <div className="fixed top-16 left-1/2 -translate-x-1/2 z-50 bg-green-900 border border-green-700 text-green-200 px-4 py-3 rounded-xl shadow-lg text-sm font-medium animate-pulse">
          Request submitted — auto-approved!
        </div>
      )}
      {/* Balance bar */}
      <div className="grid grid-cols-3 gap-2">
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-2.5 text-center">
          <p className="text-lg font-bold">6d</p>
          <p className="text-[10px] text-gray-500">PTO Left</p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-2.5 text-center">
          <p className="text-lg font-bold">2d</p>
          <p className="text-[10px] text-gray-500">Sick Left</p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-2.5 text-center">
          <p className="text-lg font-bold text-green-400">20h</p>
          <p className="text-[10px] text-gray-500">UPT Left</p>
        </div>
      </div>

      {/* Month navigation */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => setMonthOffset(monthOffset - 1)}
          className="p-2 text-gray-400 hover:text-white"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <h2 className="text-lg font-bold">{MONTHS[viewMonth]} {viewYear}</h2>
        <button
          onClick={() => setMonthOffset(monthOffset + 1)}
          className="p-2 text-gray-400 hover:text-white"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-2 text-[10px]">
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-purple-900 border border-purple-700"></span>Shift</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-gray-800 border border-gray-700"></span>Off</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-cyan-900 border border-cyan-600"></span>PTO</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-yellow-900 border border-yellow-600"></span>Limited</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-red-900 border border-red-600"></span>Blackout</span>
      </div>

      {/* Calendar grid */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-3">
        {/* Day headers */}
        <div className="grid grid-cols-7 gap-1 mb-2">
          {DAYS_OF_WEEK.map(day => (
            <div key={day} className="text-center text-[10px] text-gray-500 font-medium py-1">
              {day}
            </div>
          ))}
        </div>

        {/* Day cells */}
        <div className="grid grid-cols-7 gap-1">
          {/* Empty cells for offset */}
          {Array.from({ length: firstDayOffset }).map((_, i) => (
            <div key={`empty-${i}`} className="aspect-square" />
          ))}

          {/* Actual days */}
          {days.map((day) => {
            const isToday = day.date === today.getDate() && viewMonth === today.getMonth() && viewYear === today.getFullYear()

            return (
              <button
                key={day.date}
                onClick={() => { setSelectedDay(day); setShowRequestForm(false) }}
                className={`aspect-square rounded-lg border flex flex-col items-center justify-center relative transition
                  ${getStatusColor(day.status)}
                  ${isToday ? 'ring-2 ring-white ring-offset-1 ring-offset-gray-950' : ''}
                  ${selectedDay?.date === day.date ? 'ring-2 ring-brand-500' : ''}
                `}
              >
                <span className="text-sm font-bold">{day.date}</span>
                <span className="text-[8px] text-gray-300">{getStatusLabel(day.status)}</span>
                {day.teammatesOff && day.teammatesOff > 0 && (
                  <span className="absolute top-0.5 right-0.5 w-3.5 h-3.5 bg-yellow-600 rounded-full text-[7px] flex items-center justify-center font-bold">
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
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="font-bold">
              {MONTHS[viewMonth]} {selectedDay.date}, {viewYear}
            </h3>
            <span className={`text-xs px-2 py-0.5 rounded-full ${
              selectedDay.status === 'shift' ? 'bg-purple-900 text-purple-300' :
              selectedDay.status === 'pto_approved' ? 'bg-cyan-900 text-cyan-300' :
              selectedDay.status === 'blackout' ? 'bg-red-900 text-red-300' :
              selectedDay.status === 'limited' ? 'bg-yellow-900 text-yellow-300' :
              'bg-gray-800 text-gray-400'
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
            <div className="text-sm text-gray-400">
              <p>Shift: DA5 | 06:00 - 16:30</p>
              <p>Department: Inbound | Role: Picker</p>
            </div>
          )}

          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-400">Team coverage:</span>
            <span className={`font-medium ${
              (selectedDay.spotsRemaining ?? 0) > 2 ? 'text-green-400' :
              (selectedDay.spotsRemaining ?? 0) > 0 ? 'text-yellow-400' :
              'text-red-400'
            }`}>
              {selectedDay.spotsRemaining} spots available
            </span>
          </div>

          {selectedDay.teammatesOff && selectedDay.teammatesOff > 0 && (
            <div className="text-sm text-gray-400">
              <span className="text-yellow-400">{selectedDay.teammatesOff} teammate(s)</span> off this day
            </div>
          )}

          {/* Request PTO button */}
          {selectedDay.status !== 'blackout' && selectedDay.status !== 'pto_approved' && selectedDay.status !== 'pto_pending' && (
            <button
              onClick={() => setShowRequestForm(true)}
              className="w-full bg-brand-600 hover:bg-brand-700 py-2.5 rounded-lg font-medium text-sm transition"
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
        <div className="bg-gray-900 border border-brand-800 rounded-xl p-4 space-y-4">
          <h3 className="font-bold text-brand-400">Request Time Off</h3>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-gray-500 block mb-1">Start Date</label>
              <div className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm">
                {MONTHS[viewMonth]} {selectedDay.date}
              </div>
            </div>
            <div>
              <label className="text-xs text-gray-500 block mb-1">End Date</label>
              <div className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm">
                {MONTHS[viewMonth]} {selectedDay.date}
              </div>
            </div>
          </div>

          <div>
            <label className="text-xs text-gray-500 block mb-1">Priority</label>
            <select className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white">
              <option value="1">Priority 1 (Most important)</option>
              <option value="2">Priority 2</option>
              <option value="3">Priority 3</option>
            </select>
          </div>

          <div>
            <label className="text-xs text-gray-500 block mb-1">Reason (optional)</label>
            <input
              type="text"
              placeholder="e.g., Family event, appointment"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder:text-gray-600"
            />
          </div>

          {/* Coverage check result */}
          <div className={`rounded-lg p-3 text-sm ${
            (selectedDay.spotsRemaining ?? 0) > 1 ? 'bg-green-950 border border-green-800' :
            (selectedDay.spotsRemaining ?? 0) > 0 ? 'bg-yellow-950 border border-yellow-800' :
            'bg-red-950 border border-red-800'
          }`}>
            <p className="font-medium mb-1">
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
              className="flex-1 bg-brand-600 hover:bg-brand-700 py-2.5 rounded-lg font-medium text-sm transition"
            >
              Submit Request
            </button>
            <button
              onClick={() => setShowRequestForm(false)}
              className="flex-1 border border-gray-700 hover:border-gray-500 py-2.5 rounded-lg text-sm text-gray-300 transition"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Coverage heatmap summary */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
        <h3 className="text-sm font-medium mb-3">Coverage This Month</h3>
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-400">Best days to request off:</span>
            <span className="text-green-400 font-medium">Tue, Wed, Thu</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-400">Avoid requesting:</span>
            <span className="text-red-400 font-medium">Jul 4, Jul 25</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-400">Team size (DA5):</span>
            <span className="text-white font-medium">8 associates</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-400">Min staffing:</span>
            <span className="text-white font-medium">5 required</span>
          </div>
        </div>
      </div>
    </div>
  )
}
