import { useEffect, useRef, useState } from 'react'

function classifyEvent(text) {
  const t = text.toLowerCase()
  if (t.includes('fault') || t.includes('failed') || t.includes('warning')) return 'fault'
  if (t.includes('random event') || t.includes('resupply'))                  return 'event'
  if (t.includes('complete') || t.includes('ok') || t.includes('returned') || t.includes('green')) return 'ok'
  if (t.includes('mission') || t.includes('assigned') || t.includes('airborne')) return 'mission'
  return 'info'
}

const CLASS_COLOR = {
  fault:   'text-col-red',
  event:   'text-col-amber',
  ok:      'text-col-green',
  mission: 'text-col-blue',
  info:    'text-text-lo',
}

const FILTERS = [
  { key: 'all',     label: 'All' },
  { key: 'fault',   label: '⚠ Faults' },
  { key: 'mission', label: '✈ Missions' },
]

function fmtTime(date) {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })
}

export default function EventLog({ events }) {
  const bottomRef    = useRef(null)
  const timestampRef = useRef([])
  const [filter, setFilter] = useState('all')

  const now = new Date()
  events.forEach((_, i) => {
    if (!timestampRef.current[i]) timestampRef.current[i] = now
  })
  if (timestampRef.current.length > events.length) {
    timestampRef.current = timestampRef.current.slice(0, events.length)
  }

  const visible = events.filter(ev => filter === 'all' || classifyEvent(ev) === filter)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [events, filter])

  return (
    <div className="h-full flex flex-col bg-base">
      <div className="px-3 py-1.5 border-b border-border flex-shrink-0 flex items-center justify-between">
        <span className="text-xs text-text-dim uppercase tracking-wider">Event Log</span>
        <div className="flex gap-1">
          {FILTERS.map(f => (
            <button
              key={f.key}
              onClick={() => setFilter(f.key)}
              className={`text-xs px-2 py-0.5 rounded transition-colors
                ${filter === f.key
                  ? 'bg-raised text-text-hi border border-border'
                  : 'text-text-dim hover:text-text-lo'
                }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>
      <div className="flex-1 overflow-y-auto px-3 py-1 space-y-0.5 font-mono">
        {visible.length === 0 && (
          <div className="text-xs text-text-dim py-2">No events{filter !== 'all' ? ' matching filter' : ''}.</div>
        )}
        {events.map((ev, i) => {
          const cls = classifyEvent(ev)
          if (filter !== 'all' && cls !== filter) return null
          return (
            <div key={i} className={`text-xs leading-relaxed flex gap-2 ${CLASS_COLOR[cls]}`}>
              <span className="text-text-dim flex-shrink-0">[{fmtTime(timestampRef.current[i] ?? now)}]</span>
              <span>{ev}</span>
            </div>
          )
        })}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
