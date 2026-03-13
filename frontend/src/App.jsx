import { useState, useEffect, useCallback, useRef } from 'react'
import FleetPanel from './components/FleetPanel'
import MissionsPanel from './components/MissionsPanel'
import ResourcesPanel from './components/ResourcesPanel'
import ChatPanel from './components/ChatPanel'
import EventLog from './components/EventLog'
import ControlBar from './components/ControlBar'

const TABS = ['Fleet', 'Missions', 'Resources']

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
  const [messages, setMessages] = useState([])
  const [chatInput, setChatInput] = useState('')
  const [chatLoading, setChatLoading] = useState(false)
  const [actionLoading, setActionLoading] = useState(false)
  const [toast, setToast] = useState(null)
  const pollRef = useRef(null)

  const showToast = (msg, type = 'info') => {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 3500)
  }

  const fetchState = useCallback(async () => {
    try {
      const data = await apiFetch('/api/state')
      setState(data)
    } catch (e) {
      // silently ignore poll errors
    }
  }, [])

  useEffect(() => {
    fetchState()
    pollRef.current = setInterval(fetchState, 3000)
    return () => clearInterval(pollRef.current)
  }, [fetchState])

  const runAction = async (path, body = null) => {
    setActionLoading(true)
    try {
      const data = await apiFetch(path, {
        method: 'POST',
        body: body ? JSON.stringify(body) : undefined,
      })
      setState(data)
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
    setMessages(prev => [...prev, { role: 'user', content: msg }])
    setChatLoading(true)
    try {
      const data = await apiFetch('/api/chat', {
        method: 'POST',
        body: JSON.stringify({ message: msg }),
      })
      setMessages(prev => [...prev, { role: 'assistant', content: data.reply }])
    } catch (e) {
      setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${e.message}` }])
    } finally {
      setChatLoading(false)
    }
  }

  const clearChat = async () => {
    await apiFetch('/api/chat/clear', { method: 'POST' }).catch(() => {})
    setMessages([])
  }

  // Summary counts for header
  const ready    = state?.aircraft?.filter(a => a.status === 'green').length ?? 0
  const onMission = state?.aircraft?.filter(a => a.status === 'on_mission').length ?? 0
  const inMaint  = state?.aircraft?.filter(a => a.status === 'red').length ?? 0
  const grey     = state?.aircraft?.filter(a => a.status === 'grey').length ?? 0

  return (
    <div className="flex flex-col h-screen bg-base text-text-hi overflow-hidden">

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
                Day {state.current_day} &middot; {String(state.current_hour).padStart(2,'0')}:00
              </span>
              <span className="text-text-dim">|</span>
              <span className="uppercase tracking-widest text-col-amber font-bold">{state.phase}</span>
              <span className="text-text-dim">|</span>
              <span className="text-col-green">{ready} Ready</span>
              <span className="text-col-blue">{onMission} Flying</span>
              {inMaint > 0 && <span className="text-col-red">{inMaint} Maint</span>}
              {grey > 0 && <span className="text-text-dim">{grey} Grey</span>}
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
                Loading state...
              </div>
            )}
            {state && activeTab === 'Fleet'     && <FleetPanel state={state} />}
            {state && activeTab === 'Missions'  && (
              <MissionsPanel state={state} onAssign={(mid, aids) => runAction('/api/action/assign-aircraft', { mission_id: mid, aircraft_ids: aids })} />
            )}
            {state && activeTab === 'Resources' && <ResourcesPanel state={state} />}
          </div>

          {/* Event log */}
          <div className="flex-shrink-0 border-t border-border" style={{ height: '140px' }}>
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
        <ControlBar onAction={runAction} loading={actionLoading} />
      </div>

      {/* Toast */}
      {toast && (
        <div className={`fixed bottom-16 left-1/2 -translate-x-1/2 z-50 px-4 py-2 rounded text-sm font-semibold shadow-lg
          ${toast.type === 'error' ? 'bg-col-red text-white' : 'bg-col-blue text-white'}`}>
          {toast.msg}
        </div>
      )}
    </div>
  )
}
