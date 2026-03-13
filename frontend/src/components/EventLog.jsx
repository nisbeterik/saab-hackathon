import { useEffect, useRef } from 'react'

function classifyEvent(text) {
  const t = text.toLowerCase()
  if (t.includes('fault') || t.includes('failed') || t.includes('warning')) return 'text-col-red'
  if (t.includes('random event') || t.includes('resupply'))                  return 'text-col-amber'
  if (t.includes('complete') || t.includes('ok') || t.includes('returned') || t.includes('green')) return 'text-col-green'
  if (t.includes('mission') || t.includes('assigned') || t.includes('airborne')) return 'text-col-blue'
  return 'text-text-lo'
}

function fmtTime(date) {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })
}

export default function EventLog({ events }) {
  const bottomRef    = useRef(null)
  const timestampRef = useRef([]) // wall-clock arrival time per event index

  // Assign timestamps to newly arrived events
  const now = new Date()
  events.forEach((_, i) => {
    if (!timestampRef.current[i]) {
      timestampRef.current[i] = now
    }
  })
  // Trim if events array shrank (after reset)
  if (timestampRef.current.length > events.length) {
    timestampRef.current = timestampRef.current.slice(0, events.length)
  }

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [events])

  return (
    <div className="h-full flex flex-col bg-base">
      <div className="px-3 py-1.5 border-b border-border flex-shrink-0">
        <span className="text-xs text-text-dim uppercase tracking-wider">Event Log</span>
      </div>
      <div className="flex-1 overflow-y-auto px-3 py-1 space-y-0.5 font-mono">
        {events.length === 0 && (
          <div className="text-xs text-text-dim py-2">No events yet.</div>
        )}
        {events.map((ev, i) => (
          <div key={i} className={`text-xs leading-relaxed flex gap-2 ${classifyEvent(ev)}`}>
            <span className="text-text-dim flex-shrink-0">
              [{fmtTime(timestampRef.current[i] ?? now)}]
            </span>
            <span>{ev}</span>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
