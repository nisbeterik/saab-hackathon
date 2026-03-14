import { useState, useEffect, useCallback, useRef, createContext } from 'react'
import FleetPanel from './components/FleetPanel'
import MissionsPanel from './components/MissionsPanel'
import ScorePanel from './components/ScorePanel'
import ChatPanel from './components/ChatPanel'
import EventLog from './components/EventLog'
import ControlBar from './components/ControlBar'
import GameOverModal from './components/GameOverModal'

export const TooltipCtx = createContext(true)

const TABS = ['Fleet', 'Missions', 'Score']

function StartScreen({ onStart }) {
  return (
    <div className="flex flex-col items-center justify-center h-screen bg-base text-text-hi gap-8 px-8">
      <div className="flex flex-col items-center gap-2">
        <span className="text-col-blue font-bold text-2xl tracking-widest uppercase">SAABATH</span>
        <h1 className="text-3xl font-bold tracking-wider text-text-hi">BASED COMMANDER</h1>
        <p className="text-text-dim text-sm tracking-wide">Swedish Air Force — Dispersed Road Base Simulator</p>
      </div>
      <div className="max-w-md text-center space-y-3 text-sm text-text-lo leading-relaxed border border-border rounded-lg p-6 bg-surface">
        <p>You are the <span className="text-text-hi font-semibold">Base Battalion Commander</span> of a dispersed road base (vägbas) during a 3-day crisis escalation.</p>
        <p>Manage your Gripen fleet through three escalating phases: <span className="text-col-green font-semibold">Fred</span> → <span className="text-col-amber font-semibold">Kris</span> → <span className="text-col-red font-semibold">Krig</span>.</p>
        <p className="text-text-dim text-xs">Assign aircraft to missions, manage maintenance, conserve fuel. Your AI advisor can help — but you decide.</p>
      </div>
      <div className="flex flex-col items-center gap-3">
        <button
          onClick={onStart}
          className="px-8 py-3 bg-col-blue text-white font-bold tracking-widest uppercase rounded hover:bg-col-blue/80 transition-colors text-sm"
        >
          Begin Campaign
        </button>
        <span className="text-text-dim text-xs">Campaign length: 3 days · Starting score: 1000 · Defeat threshold: 600</span>
      </div>
    </div>
  )
}

const PHASE_DESC = {
  Fred: 'Peacetime — low readiness, normal ops',
  Kris: 'Crisis — elevated readiness, restricted comms',
  Krig: 'War — full combat ops, minimal margin for error',
}

const PHASE_COLORS = {
  Fred: 'text-col-green border-col-green/40',
  Kris: 'text-col-amber border-col-amber/40',
  Krig: 'text-col-red   border-col-red/40',
}

const AUTOPLAY_SPEEDS = [
  { key: 'normal', label: 'Normal', ms: 4000, tip: '1 game-hour every 4s — standard ops tempo' },
  { key: 'fast',   label: 'Fast',   ms: 1000, tip: '1 game-hour per second — rapid time advance' },
]
// Event probability scales with operational phase — more chaos in wartime
const AUTOPLAY_RANDOM_CHANCE = { Fred: 0.02, Kris: 0.04, Krig: 0.06 }

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
  const newWriteOff = (next.aircraft_written_off?.length ?? 0) > (prev.aircraft_written_off?.length ?? 0)
  const prevLogLen = prev.event_log?.length ?? 0
  const newScramble = (next.event_log ?? []).slice(prevLogLen).some(e => e.includes('SCRAMBLE'))
  return newFault || lifeDrop || dayRollover || missedDeparture || newWriteOff || newScramble
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

const OZZY_INTRO = {
  role: 'assistant',
  content: "I'm Ozzy Ai-rborne — Prince of Darkness, now at your service, Commander. Tell me what you need.",
}

export default function App() {
  const [gameStarted, setGameStarted] = useState(false)
  const [state, setState] = useState(null)
  const [activeTab, setActiveTab] = useState('Fleet')
  const [fleetFilter, setFleetFilter] = useState(null)
  const [messages, setMessages] = useState([{ ...OZZY_INTRO, time: new Date() }])
  const [chatInput, setChatInput] = useState('')
  const [chatLoading, setChatLoading] = useState(false)
  const [actionLoading, setActionLoading] = useState(false)
  const [toast, setToast] = useState(null)
  const [backendError, setBackendError] = useState(false)
  const [tooltipsEnabled, setTooltipsEnabled] = useState(true)
  const [autoplay, setAutoplay] = useState(false)
  const [autoplaySpeedIdx, setAutoplaySpeedIdx] = useState(0)
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
        const eventChance = AUTOPLAY_RANDOM_CHANCE[next.phase] ?? 0.04
        if (Math.random() < eventChance) {
          const withEvent = await apiFetch('/api/action/random-event', { method: 'POST' })
          setState(withEvent)
          const lastEvent = withEvent.event_log?.[withEvent.event_log.length - 1]
          if (lastEvent) showToast(lastEvent, 'info')
          checkState = withEvent
        }
        if (checkState.campaign_over) {
          setAutoplay(false)
        } else if (isCritical(prev, checkState)) {
          setAutoplay(false)
          const newFaultAc = checkState.aircraft.find(a => {
            const p = prev?.aircraft?.find(p => p.id === a.id)
            return a.status === 'red' && p && p.status !== 'red'
          })
          const lifeDrop = checkState.aircraft.find(a => {
            const p = prev?.aircraft?.find(p => p.id === a.id)
            return p && p.remaining_life > 20 && a.remaining_life <= 20
          })
          const prevLogLen = prev?.event_log?.length ?? 0
          const scrambleEvent = (checkState.event_log ?? []).slice(prevLogLen).find(e => e.includes('SCRAMBLE'))
          const pauseReason = checkState.current_day !== prev?.current_day
            ? `Day ${checkState.current_day} — new ATO generated`
            : scrambleEvent ? scrambleEvent
            : newFaultAc ? `${newFaultAc.id} fault — check fleet`
            : lifeDrop ? `${lifeDrop.id} life critical (${lifeDrop.remaining_life}h)`
            : 'Critical event'
          showToast(`⏸ Paused — ${pauseReason}`, 'info')
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
  }, [actionLoading])

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
        setMessages([{ ...OZZY_INTRO, time: new Date() }])
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
    setMessages([{ ...OZZY_INTRO, time: new Date() }])
  }

  const ready     = state?.aircraft?.filter(a => a.status === 'green').length ?? 0
  const onMission = state?.aircraft?.filter(a => a.status === 'on_mission').length ?? 0
  const inMaint   = state?.aircraft?.filter(a => a.status === 'red').length ?? 0
  const grey      = state?.aircraft?.filter(a => a.status === 'grey').length ?? 0

  if (!gameStarted) {
    return <StartScreen onStart={() => setGameStarted(true)} />
  }

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
          <span className="text-col-blue font-bold text-sm tracking-widest uppercase">SAABATH</span>
          <span className="text-text-dim">|</span>
          <span className="font-semibold text-sm tracking-wider">BASED COMMANDER</span>
        </div>
        <div className="flex items-center gap-4 text-xs text-text-lo">
          {state && (
            <>
              <span className="text-text-hi font-semibold">
                Day {state.current_day} &middot; {String(state.current_hour).padStart(2, '0')}:00
              </span>
              <span className="text-text-dim">|</span>
              <span
                title={PHASE_DESC[state.phase] ?? ''}
                className={`uppercase tracking-widest font-bold ${PHASE_COLORS[state.phase]?.split(' ')[0] ?? 'text-col-amber'}`}
              >
                {state.phase}
              </span>
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
              {(state.aircraft_written_off?.length ?? 0) > 0 && (
                <span
                  className="text-col-red/70 cursor-pointer hover:underline"
                  onClick={() => { setActiveTab('Fleet'); setFleetFilter('written_off') }}
                >{state.aircraft_written_off.length} Lost</span>
              )}
              <span className="text-text-dim">|</span>
              {/* Campaign score */}
              <span
                className={`font-bold cursor-pointer hover:underline ${
                  state.campaign_score >= 800 ? 'text-col-green' :
                  state.campaign_score >= 700 ? 'text-col-amber' :
                  state.campaign_score >= 600 ? 'text-col-red' : 'text-col-red animate-pulse'
                }`}
                onClick={() => setActiveTab('Score')}
                title={state.campaign_grade}
              >
                {state.campaign_score}pts
              </span>
              <span className="text-text-dim">Day {state.current_day}/3</span>
              <span className="text-text-dim">|</span>
              {/* Fuel indicator + resupply */}
              {(() => {
                const fuel    = state.resources?.fuel ?? 0
                const sorties = Math.floor(fuel / 4000)
                const fuelCol = sorties > 20 ? 'text-col-green' : sorties > 8 ? 'text-col-amber' : 'text-col-red animate-pulse'
                return (
                  <>
                    <span className={`font-semibold ${fuelCol}`} title={`${fuel.toLocaleString()}L fuel available`}>
                      ⛽ {sorties} sorties
                    </span>
                    {state.resupply_eta != null
                      ? <span className="text-col-green text-xs animate-pulse" title={`Convoy arrives in ${state.resupply_eta}h — +30,000L fuel`}>
                          Convoy {state.resupply_eta}h
                        </span>
                      : <button
                          onClick={() => runAction('/api/action/request-resupply')}
                          disabled={actionLoading}
                          className="text-xs px-1.5 py-0.5 rounded border border-col-green/40 text-col-green hover:bg-col-green/10 disabled:opacity-40 transition-colors"
                          title="Request resupply convoy — +30,000L fuel in 8h"
                        >
                          Resupply
                        </button>
                    }
                  </>
                )
              })()}
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
            {state && activeTab === 'Score'     && <ScorePanel state={state} />}
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
          />
        </div>
      </div>

      {/* Control bar */}
      <div className="flex-shrink-0 border-t border-border bg-surface px-3 py-2">
        <ControlBar
          onAction={runAction}
          loading={actionLoading}
          autoplay={autoplay}
          onToggleAutoplay={() => setAutoplay(v => !v)}
          autoplaySpeedIdx={autoplaySpeedIdx}
          onCycleSpeed={() => setAutoplaySpeedIdx(i => (i + 1) % AUTOPLAY_SPEEDS.length)}
          autoplaySpeeds={AUTOPLAY_SPEEDS}
        />
      </div>

      {/* Toast */}
      {toast && (
        <div className={`fixed bottom-16 left-1/2 -translate-x-1/2 z-50 px-4 py-2 rounded text-xs font-semibold shadow-lg max-w-sm text-center
          ${toast.type === 'error' ? 'bg-col-red text-white' : 'bg-raised border border-border text-text-hi'}`}>
          {toast.msg}
        </div>
      )}

      {/* Game Over / Victory modal */}
      <GameOverModal
        state={state}
        onReset={() => runAction('/api/action/reset')}
      />
    </div>
    </TooltipCtx.Provider>
  )
}
