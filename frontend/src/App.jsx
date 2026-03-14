import { useState, useEffect, useCallback, useRef, createContext } from 'react'
import FleetPanel from './components/FleetPanel'
import MissionsPanel from './components/MissionsPanel'
import ResourcesPanel from './components/ResourcesPanel'
import ChatPanel from './components/ChatPanel'
import EventLog from './components/EventLog'
import ControlBar from './components/ControlBar'

export const TooltipCtx = createContext(true)

const TABS = ['Fleet', 'Missions', 'Resources']

const PHASE_DESC = {
  Fred: 'Peacetime — low readiness, normal ops',
  Kris: 'Crisis — elevated readiness, restricted comms',
  Krig: 'War — full combat ops, minimal margin for error',
}

const PHASE_CYCLE = ['Fred', 'Kris', 'Krig']
const PHASE_COLORS = {
  Fred: 'text-col-green border-col-green/40',
  Kris: 'text-col-amber border-col-amber/40',
  Krig: 'text-col-red   border-col-red/40',
}

const AUTOPLAY_SPEEDS = [
  { key: 'x1',  label: '×1 Slow',   ms: 60000, tip: '1 game-hour per minute — relaxed pace' },
  { key: 'x2',  label: '×2 Normal', ms: 30000, tip: '1 game-hour every 30s — standard ops tempo' },
  { key: 'x4',  label: '×4 Fast',   ms: 15000, tip: '1 game-hour every 15s — accelerated planning' },
  { key: 'x15', label: '×15 Blitz', ms:  4000, tip: '1 game-hour every 4s — rapid skip-ahead' },
]
const AUTOPLAY_RANDOM_CHANCE = 0.04

function isCritical(prev, next) {
  if (!prev || !next) return false
  const prevRedIds = new Set(prev.aircraft.filter(a => a.status === 'red').map(a => a.id))
  const newFault = next.aircraft.some(a => a.status === 'red' && !prevRedIds.has(a.id))
  const lifeDrop = next.aircraft.some(a => {
    const p = prev.aircraft.find(p => p.id === a.id)
    return p && p.remaining_life > 20 && a.remaining_life <= 20
  })
  const dayRollover = next.current_day !== prev.current_day
  const missedDeparture = !dayRollover && (next.ato?.missions ?? []).some(m =>
    m.assigned_aircraft?.length === 0 &&
    prev.current_hour < m.departure_hour &&
    next.current_hour >= m.departure_hour
  )
  return newFault || lifeDrop || dayRollover || missedDeparture
}

async function apiFetch(path, options = {}) {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || res.statusText)
  }
  return res.json()
}

export default function App() {
  const [state, setState] = useState(null)
  const [activeTab, setActiveTab] = useState('Fleet')
  const [fleetFilter, setFleetFilter] = useState(null)
  const [messages, setMessages] = useState([])
  const [chatInput, setChatInput] = useState('')
  const [chatLoading, setChatLoading] = useState(false)
  const [actionLoading, setActionLoading] = useState(false)
  const [toast, setToast] = useState(null)
  const [backendError, setBackendError] = useState(false)
  const [tooltipsEnabled, setTooltipsEnabled] = useState(true)
  const [demoScenarios, setDemoScenarios] = useState([])
  const [autoplay, setAutoplay] = useState(false)
  const [autoplaySpeedIdx, setAutoplaySpeedIdx] = useState(0)
  const [autoplayRandomEvents, setAutoplayRandomEvents] = useState(false)
  const pollRef = useRef(null)
  const autoplayRef = useRef(null)
  const prevStateRef = useRef(null)
  const isTickRunning = useRef(false)
  const autoplayTickFnRef = useRef(null)

  const showToast = (msg, type = 'info') => {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 4000)
  }

  const fetchState = useCallback(async () => {
    try {
      const data = await apiFetch('/api/state')
      setState(data)
      setBackendError(false)
    } catch {
      setBackendError(true)
    }
  }, [])

  useEffect(() => {
    fetchState()
    pollRef.current = setInterval(fetchState, 3000)

    const onVisibility = () => {
      if (document.hidden) {
        clearInterval(pollRef.current)
      } else {
        fetchState()
        pollRef.current = setInterval(fetchState, 3000)
      }
    }
    document.addEventListener('visibilitychange', onVisibility)
    return () => {
      clearInterval(pollRef.current)
      document.removeEventListener('visibilitychange', onVisibility)
    }
  }, [fetchState])

  // Fetch demo script once on mount
  useEffect(() => {
    apiFetch('/api/demo/scenarios').then(setDemoScenarios).catch(() => {})
  }, [])

  // Keep the autoplay tick fn fresh so it always closes over latest state
  useEffect(() => {
    autoplayTickFnRef.current = async () => {
      if (isTickRunning.current || actionLoading) return
      isTickRunning.current = true
      const prev = prevStateRef.current
      try {
        const next = await apiFetch('/api/action/advance-time', {
          method: 'POST',
          body: JSON.stringify({ hours: 1 }),
        })
        setState(next)
        let checkState = next
        if (autoplayRandomEvents && Math.random() < AUTOPLAY_RANDOM_CHANCE) {
          const withEvent = await apiFetch('/api/action/random-event', { method: 'POST' })
          setState(withEvent)
          const lastEvent = withEvent.event_log?.[withEvent.event_log.length - 1]
          if (lastEvent) showToast(lastEvent, 'info')
          checkState = withEvent
        }
        if (isCritical(prev, checkState)) {
          setAutoplay(false)
          showToast('⏸ Autoplay paused — critical event', 'info')
        } else {
          prevStateRef.current = checkState
        }
      } catch (e) {
        setAutoplay(false)
        showToast(`Autoplay stopped: ${e.message}`, 'error')
      } finally {
        isTickRunning.current = false
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoplayRandomEvents, actionLoading])

  // Start/stop autoplay interval when play state or speed changes
  useEffect(() => {
    if (!autoplay) {
      clearInterval(autoplayRef.current)
      return
    }
    prevStateRef.current = state
    autoplayRef.current = setInterval(
      () => autoplayTickFnRef.current?.(),
      AUTOPLAY_SPEEDS[autoplaySpeedIdx].ms,
    )
    return () => clearInterval(autoplayRef.current)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoplay, autoplaySpeedIdx])

  const runAction = async (path, body = null) => {
    setActionLoading(true)
    try {
      const data = await apiFetch(path, {
        method: 'POST',
        body: body ? JSON.stringify(body) : undefined,
      })
      setState(data)
      // Clear frontend chat when state resets (backend already cleared LLM history)
      if (path === '/api/action/reset' && data.chat_cleared) {
        setMessages([])
      }
      // Surface what the random event actually was
      if (path === '/api/action/random-event' && data.event_log?.length) {
        showToast(data.event_log[data.event_log.length - 1], 'info')
      }
    } catch (e) {
      showToast(e.message, 'error')
    } finally {
      setActionLoading(false)
    }
  }

  const sendChat = async () => {
    const msg = chatInput.trim()
    if (!msg || chatLoading) return
    setChatInput('')
    setMessages(prev => [...prev, { role: 'user', content: msg, time: new Date() }])
    setChatLoading(true)
    try {
      const data = await apiFetch('/api/chat', {
        method: 'POST',
        body: JSON.stringify({ message: msg }),
      })
      setMessages(prev => [...prev, { role: 'assistant', content: data.reply, time: new Date() }])
    } catch (e) {
      setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${e.message}`, time: new Date() }])
    } finally {
      setChatLoading(false)
    }
  }

  const clearChat = async () => {
    await apiFetch('/api/chat/clear', { method: 'POST' }).catch(() => {})
    setMessages([])
  }

  // Run a demo script step: apply event trigger on backend, update state, pre-fill chat input
  const runDemoStep = async (label) => {
    setActionLoading(true)
    try {
      const data = await apiFetch('/api/demo/run', {
        method: 'POST',
        body: JSON.stringify({ label }),
      })
      setState(data.state)
      setChatInput(data.question)
    } catch (e) {
      showToast(e.message, 'error')
    } finally {
      setActionLoading(false)
    }
  }

  const ready     = state?.aircraft?.filter(a => a.status === 'green').length ?? 0
  const onMission = state?.aircraft?.filter(a => a.status === 'on_mission').length ?? 0
  const inMaint   = state?.aircraft?.filter(a => a.status === 'red').length ?? 0
  const grey      = state?.aircraft?.filter(a => a.status === 'grey').length ?? 0

  return (
    <TooltipCtx.Provider value={tooltipsEnabled}>
    <div className="flex flex-col h-screen bg-base text-text-hi overflow-hidden">

      {/* Backend error banner */}
      {backendError && (
        <div className="flex-shrink-0 bg-col-red/20 border-b border-col-red/50 px-4 py-1.5 text-xs text-col-red font-semibold text-center">
          ⚠ Backend unreachable — retrying... Check that the API server is running.
        </div>
      )}

      {/* Header */}
      <header className="flex items-center justify-between px-4 py-2 bg-surface border-b border-border flex-shrink-0">
        <div className="flex items-center gap-3">
          <span className="text-col-blue font-bold text-sm tracking-widest uppercase">SAAB</span>
          <span className="text-text-dim">|</span>
          <span className="font-semibold text-sm tracking-wider">BASE COMMANDER</span>
        </div>
        <div className="flex items-center gap-4 text-xs text-text-lo">
          {state && (
            <>
              <span className="text-text-hi font-semibold">
                Day {state.current_day} &middot; {String(state.current_hour).padStart(2, '0')}:00
              </span>
              <span className="text-text-dim">|</span>
              <button
                onClick={() => {
                  const next = PHASE_CYCLE[(PHASE_CYCLE.indexOf(state.phase) + 1) % 3]
                  runAction('/api/action/set-phase', { phase: next })
                }}
                disabled={actionLoading}
                title={`${PHASE_DESC[state.phase] ?? ''} — click to escalate`}
                className={`uppercase tracking-widest font-bold border-b border-dashed transition-colors
                  hover:opacity-70 disabled:opacity-40 cursor-pointer
                  ${PHASE_COLORS[state.phase] ?? 'text-col-amber border-col-amber/40'}`}
              >
                {state.phase}
              </button>
              <span className="text-text-dim">|</span>
              <button
                onClick={() => setTooltipsEnabled(v => !v)}
                className={`text-xs px-2 py-0.5 rounded border transition-colors
                  ${tooltipsEnabled ? 'border-col-blue/50 text-col-blue' : 'border-border text-text-dim'}`}
                title="Toggle help tooltips on acronyms and terms"
              >
                {tooltipsEnabled ? 'ⓘ Help ON' : 'ⓘ Help OFF'}
              </button>
              <span className="text-text-dim">|</span>
              <span
                className="text-col-green cursor-pointer hover:underline"
                onClick={() => { setActiveTab('Fleet'); setFleetFilter('green') }}
              >{ready} Ready</span>
              <span
                className="text-col-blue cursor-pointer hover:underline"
                onClick={() => { setActiveTab('Fleet'); setFleetFilter('on_mission') }}
              >{onMission} Flying</span>
              {inMaint > 0 && (
                <span
                  className="text-col-red cursor-pointer hover:underline"
                  onClick={() => { setActiveTab('Fleet'); setFleetFilter('red') }}
                >{inMaint} Maint</span>
              )}
              {grey > 0 && (
                <span
                  className="text-text-dim cursor-pointer hover:underline"
                  onClick={() => { setActiveTab('Fleet'); setFleetFilter('grey') }}
                >{grey} Grey</span>
              )}
            </>
          )}
          {!state && <span className="text-text-dim animate-pulse">Connecting...</span>}
        </div>
      </header>

      {/* Main layout */}
      <div className="flex flex-1 overflow-hidden">

        {/* Left: Tabs + content + event log */}
        <div className="flex flex-col flex-1 overflow-hidden border-r border-border">

          {/* Tab bar */}
          <div className="flex items-center gap-1 px-3 pt-2 pb-0 bg-surface border-b border-border flex-shrink-0">
            {TABS.map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-1.5 text-xs font-semibold tracking-wider uppercase rounded-t transition-colors
                  ${activeTab === tab
                    ? 'bg-base text-text-hi border border-b-0 border-border'
                    : 'text-text-lo hover:text-text-hi'
                  }`}
              >
                {tab}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div className="flex-1 overflow-y-auto p-3 bg-base">
            {!state && (
              <div className="flex items-center justify-center h-full text-text-dim text-sm">
                {backendError ? 'Backend unreachable.' : 'Loading state...'}
              </div>
            )}
            {state && activeTab === 'Fleet'     && (
              <FleetPanel
                state={state}
                onAction={runAction}
                fleetFilter={fleetFilter}
                onClearFilter={() => setFleetFilter(null)}
              />
            )}
            {state && activeTab === 'Missions'  && (
              <MissionsPanel
                state={state}
                onAssign={(mid, aids) => runAction('/api/action/assign-aircraft', { mission_id: mid, aircraft_ids: aids })}
              />
            )}
            {state && activeTab === 'Resources' && <ResourcesPanel state={state} />}
          </div>

          {/* Event log */}
          <div className="flex-shrink-0 border-t border-border" style={{ height: '180px' }}>
            <EventLog events={state?.event_log ?? []} />
          </div>
        </div>

        {/* Right: Chat */}
        <div className="flex-shrink-0 flex flex-col bg-surface" style={{ width: '360px' }}>
          <ChatPanel
            messages={messages}
            input={chatInput}
            loading={chatLoading}
            onInputChange={setChatInput}
            onSend={sendChat}
            onClear={clearChat}
            scenarios={demoScenarios}
            onRunScenario={runDemoStep}
            actionLoading={actionLoading}
          />
        </div>
      </div>

      {/* Control bar */}
      <div className="flex-shrink-0 border-t border-border bg-surface px-3 py-2">
        <ControlBar
          onAction={runAction}
          loading={actionLoading}
          scenarios={[demoScenarios[0], demoScenarios[2], demoScenarios[3]].filter(Boolean)}
          onRunScenario={runDemoStep}
          autoplay={autoplay}
          onToggleAutoplay={() => setAutoplay(v => !v)}
          autoplaySpeedIdx={autoplaySpeedIdx}
          onCycleSpeed={() => setAutoplaySpeedIdx(i => (i + 1) % AUTOPLAY_SPEEDS.length)}
          autoplaySpeeds={AUTOPLAY_SPEEDS}
          autoplayRandomEvents={autoplayRandomEvents}
          onToggleRandomEvents={() => setAutoplayRandomEvents(v => !v)}
        />
      </div>

      {/* Toast */}
      {toast && (
        <div className={`fixed bottom-16 left-1/2 -translate-x-1/2 z-50 px-4 py-2 rounded text-xs font-semibold shadow-lg max-w-sm text-center
          ${toast.type === 'error' ? 'bg-col-red text-white' : 'bg-raised border border-border text-text-hi'}`}>
          {toast.msg}
        </div>
      )}
    </div>
    </TooltipCtx.Provider>
  )
}
