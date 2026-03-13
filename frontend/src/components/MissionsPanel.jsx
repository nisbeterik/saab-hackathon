import { useState } from 'react'

const TYPE_COLOR = {
  DCA:    'text-col-blue',
  RECCE:  'text-col-amber',
  'AI/ST': 'text-col-red',
  QRA:    'text-col-green',
  AEW:    'text-text-lo',
}

const TYPE_BG = {
  DCA:    '#1f6feb',
  RECCE:  '#d29922',
  'AI/ST': '#f85149',
  QRA:    '#3fb950',
  AEW:    '#484f58',
}

function pad(n) {
  return String(n).padStart(2, '0')
}

function MissionRow({ mission }) {
  const assigned = mission.assigned_aircraft ?? []
  const needed   = mission.required_aircraft - assigned.length
  const full     = needed <= 0

  return (
    <div className={`bg-surface border rounded p-3 space-y-2 ${full ? 'border-border' : 'border-col-amber/50'}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="font-bold text-text-hi text-sm">{mission.id}</span>
          <span className={`text-xs font-bold tracking-wider ${TYPE_COLOR[mission.type] ?? 'text-text-lo'}`}>{mission.type}</span>
        </div>
        <div className={`text-xs font-semibold px-1.5 py-0.5 rounded ${full ? 'text-col-green bg-col-green/10' : 'text-col-amber bg-col-amber/10'}`}>
          {assigned.length}/{mission.required_aircraft} {full ? '✓ ASSIGNED' : `⚠ NEED ${needed}`}
        </div>
      </div>

      {mission.description && (
        <div className="text-xs text-text-dim">{mission.description}</div>
      )}

      <div className="flex items-center gap-4 text-xs">
        <span className="text-text-lo">
          Dep <span className="text-text-hi font-semibold">{pad(mission.departure_hour)}:00</span>
        </span>
        <span className="text-text-dim">→</span>
        <span className="text-text-lo">
          Ret <span className="text-text-hi font-semibold">{pad(mission.return_hour)}:00</span>
        </span>
        <span className="ml-auto text-text-dim">{mission.required_config}</span>
      </div>

      {assigned.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {assigned.map(id => (
            <span key={id} className="px-1.5 py-0.5 bg-col-blue/10 border border-col-blue/30 text-col-blue text-xs rounded">
              {id}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

export default function MissionsPanel({ state, onAssign }) {
  const missions = state?.ato?.missions ?? []
  const aircraft = state?.aircraft ?? []

  const [selectedMission, setSelectedMission]   = useState('')
  const [selectedAircraft, setSelectedAircraft] = useState([])
  const [assigning, setAssigning]               = useState(false)
  const [error, setError]                       = useState(null)

  const greenAircraft      = aircraft.filter(a => a.status === 'green')
  const selectedMissionObj = missions.find(m => m.id === selectedMission)

  const handleAssign = async () => {
    if (!selectedMission || selectedAircraft.length === 0) return
    setAssigning(true)
    setError(null)
    try {
      await onAssign(selectedMission, selectedAircraft)
      setSelectedAircraft([])
      setSelectedMission('')
    } catch (e) {
      setError(e.message)
    } finally {
      setAssigning(false)
    }
  }

  const toggleAircraft = (id) => {
    setSelectedAircraft(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    )
  }

  const hasMismatch = selectedAircraft.some(id => {
    const ac = greenAircraft.find(a => a.id === id)
    return ac && selectedMissionObj && ac.configuration !== selectedMissionObj.required_config
  })

  return (
    <div className="space-y-4">

      {/* ATO Coverage summary */}
      {(() => {
        const total    = missions.length
        const covered  = missions.filter(m => (m.assigned_aircraft ?? []).length >= m.required_aircraft).length
        const partial  = missions.filter(m => (m.assigned_aircraft ?? []).length > 0 && (m.assigned_aircraft ?? []).length < m.required_aircraft).length
        const missing  = missions.filter(m => (m.assigned_aircraft ?? []).length === 0).length
        const allGood  = covered === total
        return (
          <div className={`border rounded p-3 flex items-center gap-4 ${allGood ? 'bg-col-green/5 border-col-green/30' : 'bg-col-amber/5 border-col-amber/30'}`}>
            <div className="flex-1">
              <div className={`text-xs font-bold uppercase tracking-wider mb-1 ${allGood ? 'text-col-green' : 'text-col-amber'}`}>
                ATO Coverage
              </div>
              <div className="flex gap-3 text-xs">
                <span className="text-col-green">{covered} fully assigned</span>
                {partial > 0 && <span className="text-col-amber">{partial} partial</span>}
                {missing > 0 && <span className="text-col-red">{missing} unassigned</span>}
              </div>
            </div>
            <div className="flex gap-1">
              {missions.map(m => {
                const assigned = m.assigned_aircraft ?? []
                const full = assigned.length >= m.required_aircraft
                const none = assigned.length === 0
                const color = full ? 'bg-col-green' : none ? 'bg-col-red' : 'bg-col-amber'
                return (
                  <div key={m.id} className="flex flex-col items-center gap-0.5" title={`${m.id} ${m.type}: ${assigned.length}/${m.required_aircraft}`}>
                    <div className={`w-2 h-2 rounded-full ${color}`} />
                    <span className="text-xs text-text-dim" style={{ fontSize: '9px' }}>{m.id}</span>
                  </div>
                )
              })}
            </div>
          </div>
        )
      })()}

      {/* Gantt timeline */}
      <div className="bg-surface border border-border rounded p-3">
        <div className="text-xs text-text-dim uppercase tracking-wider mb-3">
          ATO Timeline — Day {state?.ato?.day} ({state?.ato?.phase})
        </div>

        {/* Hour ruler — absolutely positioned for accurate alignment with bars */}
        <div className="flex mb-2">
          <div className="w-20 flex-shrink-0" />
          <div className="flex-1 relative h-4">
            {[0, 6, 12, 18, 24].map(h => (
              <span
                key={h}
                className="absolute text-xs text-text-dim select-none"
                style={{ left: `${(h / 24) * 100}%`, transform: 'translateX(-50%)' }}
              >
                {pad(h)}
              </span>
            ))}
          </div>
        </div>

        {/* Mission bars */}
        {missions.map(m => {
          const start      = (m.departure_hour / 24) * 100
          const width      = Math.max(2, ((m.return_hour - m.departure_hour) / 24) * 100)
          const assigned   = m.assigned_aircraft ?? []
          const unassigned = assigned.length === 0
          const barColor   = unassigned ? '#f85149' : (TYPE_BG[m.type] ?? '#484f58')

          return (
            <div key={m.id} className="flex items-center mb-1.5">
              <div className="w-20 flex-shrink-0 text-xs flex items-center gap-1">
                <span className="text-text-lo">{m.id}</span>
                <span className={`font-bold ${TYPE_COLOR[m.type] ?? 'text-text-lo'}`}>{m.type}</span>
              </div>
              <div className="flex-1 h-5 bg-raised rounded relative">
                <div
                  className="absolute h-full rounded flex items-center px-1.5 text-xs font-semibold text-white overflow-hidden whitespace-nowrap"
                  style={{ left: `${start}%`, width: `${width}%`, backgroundColor: barColor, opacity: 0.9 }}
                >
                  {unassigned ? 'UNASSIGNED' : assigned.join(' ')}
                </div>
              </div>
            </div>
          )
        })}

        {/* Current time marker */}
        {state && (
          <div className="flex items-center mt-1">
            <div className="w-20 flex-shrink-0 text-xs text-col-amber font-semibold">Now</div>
            <div className="flex-1 h-5 relative">
              <div
                className="absolute top-0 bottom-0 w-0.5 bg-col-amber opacity-80"
                style={{ left: `${(state.current_hour / 24) * 100}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Mission cards */}
      <div className="grid grid-cols-2 gap-2">
        {missions.map(m => <MissionRow key={m.id} mission={m} />)}
      </div>

      {/* Assign form */}
      <div className="bg-surface border border-border rounded p-3 space-y-3">
        <div className="text-xs text-text-dim uppercase tracking-wider">Assign Aircraft to Mission</div>

        <div>
          <label className="text-xs text-text-lo mb-1 block">Mission</label>
          <select
            value={selectedMission}
            onChange={e => { setSelectedMission(e.target.value); setSelectedAircraft([]) }}
            className="w-full bg-raised border border-border rounded px-2 py-1.5 text-sm text-text-hi focus:outline-none focus:border-col-blue"
          >
            <option value="">— select mission —</option>
            {missions.map(m => (
              <option key={m.id} value={m.id}>
                {m.id} | {m.type} | {pad(m.departure_hour)}:00 — {m.required_config}
              </option>
            ))}
          </select>
        </div>

        {selectedMissionObj && (
          <div className="text-xs text-text-dim bg-raised border border-border rounded px-2 py-1.5">
            Requires config: <span className="text-col-amber font-semibold">{selectedMissionObj.required_config}</span>
            {' · '}needs <span className="text-text-hi font-semibold">{selectedMissionObj.required_aircraft}</span> aircraft
          </div>
        )}

        <div>
          <label className="text-xs text-text-lo mb-1 block">Aircraft (ready only)</label>
          <div className="flex flex-wrap gap-1.5">
            {greenAircraft.length === 0 && (
              <span className="text-xs text-text-dim">No ready aircraft available</span>
            )}
            {greenAircraft.map(ac => {
              const mismatch = selectedMissionObj && ac.configuration !== selectedMissionObj.required_config
              const selected = selectedAircraft.includes(ac.id)
              return (
                <button
                  key={ac.id}
                  onClick={() => toggleAircraft(ac.id)}
                  title={mismatch ? `Config mismatch: ${ac.configuration} ≠ ${selectedMissionObj.required_config}` : ac.configuration}
                  className={`px-2 py-0.5 rounded text-xs font-semibold border transition-colors
                    ${selected
                      ? 'bg-col-blue/20 border-col-blue text-col-blue'
                      : mismatch
                        ? 'bg-raised border-col-amber/40 text-col-amber hover:border-col-amber'
                        : 'bg-raised border-border text-text-lo hover:border-col-blue/50 hover:text-text-hi'
                    }`}
                >
                  {ac.id}
                  <span className="ml-1 opacity-60">{ac.configuration}</span>
                  {mismatch && <span className="ml-1">⚠</span>}
                </button>
              )
            })}
          </div>
        </div>

        {hasMismatch && (
          <div className="text-xs text-col-amber bg-col-amber/10 border border-col-amber/30 rounded px-2 py-1.5">
            ⚠ Selected aircraft have mismatched configs — reconfiguration required before departure.
          </div>
        )}

        {error && (
          <div className="text-xs text-col-red bg-col-red/10 border border-col-red/30 rounded px-2 py-1">
            {error}
          </div>
        )}

        <button
          onClick={handleAssign}
          disabled={!selectedMission || selectedAircraft.length === 0 || assigning}
          className="w-full py-1.5 bg-col-blue text-white text-xs font-bold tracking-wider uppercase rounded
            hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          {assigning
            ? 'Assigning...'
            : selectedAircraft.length > 0
              ? `Assign ${selectedAircraft.join(', ')}`
              : 'Assign'}
        </button>
      </div>
    </div>
  )
}
