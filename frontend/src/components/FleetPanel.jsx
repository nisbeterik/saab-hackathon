import { useContext } from 'react'
import { TooltipCtx } from '../App'
import Tooltip from './Tooltip'
import { GLOSSARY } from '../tooltips'

const STATUS_CONFIG = {
  green:      { label: 'READY',     color: 'text-col-green',  dot: 'bg-col-green',  border: 'border-col-green/30'  },
  red:        { label: 'MAINT',     color: 'text-col-red',    dot: 'bg-col-red',    border: 'border-col-red/30'    },
  grey:       { label: 'GREY',      color: 'text-text-dim',   dot: 'bg-text-dim',   border: 'border-border'         },
  on_mission: { label: 'AIRBORNE',  color: 'text-col-blue',   dot: 'bg-col-blue',   border: 'border-col-blue/30'   },
  returning:  { label: 'RETURNING', color: 'text-col-cyan',   dot: 'bg-col-cyan',   border: 'border-col-cyan/30'   },
}

// Top-down pixel-art Gripen — grey only, traced from reference image
function JetIcon() {
  const s = 1
  const T = null
  const A = '#1e1e2c'  // darkest — cockpit glass, engine interior
  const B = '#3e3e56'  // dark — engine pods, shadow panels
  const C = '#606078'  // mid — main body
  const D = '#848498'  // light — surface highlights, leading edges
  const W = '#d0d8ec'  // near-white — cockpit highlight, exhaust glow

  // 18 wide × 20 tall
  const grid = [
    [T, T, T, T, T, T, T, T, C, C, T, T, T, T, T, T, T, T],  // nose tip
    [T, T, T, T, T, T, T, C, C, C, C, T, T, T, T, T, T, T],  // nose
    [T, T, T, T, T, T, C, C, A, A, C, C, T, T, T, T, T, T],  // canopy dark
    [T, T, T, T, T, T, C, C, A, A, C, C, T, T, T, T, T, T],  // canopy dark
    [T, T, T, T, T, C, C, C, W, W, C, C, C, T, T, T, T, T],  // canopy white
    [T, T, T, T, T, C, C, C, B, B, C, C, C, T, T, T, T, T],  // canopy base
    [T, T, T, T, C, C, C, C, C, C, C, C, C, C, T, T, T, T],  // body widens
    [T, T, T, C, C, D, C, C, C, C, C, C, D, C, C, T, T, T],  // wing leading
    [T, T, C, C, D, D, C, C, C, C, C, C, D, D, C, C, T, T],  // wings grow
    [T, C, C, D, D, C, C, C, C, C, C, C, C, D, D, C, C, T],
    [C, C, D, D, C, C, C, C, C, C, C, C, C, C, D, D, C, C],  // max span
    [C, C, D, C, C, C, C, C, C, C, C, C, C, C, C, D, C, C],
    [T, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, T],  // wings taper
    [T, T, C, C, C, C, C, C, C, C, C, C, C, C, C, C, T, T],
    [T, T, T, C, C, C, C, C, C, C, C, C, C, C, C, T, T, T],
    [T, T, T, T, C, C, C, C, C, C, C, C, C, C, T, T, T, T],  // waist
    [T, T, T, T, T, C, B, B, C, C, B, B, C, T, T, T, T, T],  // engine pods
    [T, T, T, T, T, C, B, A, C, C, A, B, C, T, T, T, T, T],  // engine interior
    [T, T, T, T, T, T, B, A, C, C, A, B, T, T, T, T, T, T],  // nozzle
    [T, T, T, T, T, T, W, W, T, T, W, W, T, T, T, T, T, T],  // exhaust glow
  ]

  return (
    <svg
      width={18 * s} height={20 * s}
      style={{ imageRendering: 'pixelated', verticalAlign: 'middle' }}
      aria-hidden="true"
    >
      {grid.flatMap((row, ri) =>
        row.map((color, ci) =>
          color ? <rect key={`${ri}-${ci}`} x={ci * s} y={ri * s} width={s} height={s} fill={color} /> : null
        )
      )}
    </svg>
  )
}

function lifeColor(life) {
  if (life > 100) return 'bg-col-green'
  if (life > 30)  return 'bg-col-amber'
  return 'bg-col-red'
}

function lifeTextColor(life) {
  if (life > 100) return 'text-col-green'
  if (life > 30)  return 'text-col-amber'
  return 'text-col-red'
}

function AircraftCard({ ac, mission, onAction }) {
  const s = STATUS_CONFIG[ac.status] ?? STATUS_CONFIG.grey
  const tooltipsEnabled = useContext(TooltipCtx)
  const lifePct = Math.min(100, Math.round((ac.remaining_life / 200) * 100))

  return (
    <div className={`bg-surface border ${s.border} rounded p-3 flex flex-col gap-1.5`}>
      {/* Header row */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full flex-shrink-0 ${s.dot} ${ac.status === 'on_mission' ? 'pulse-dot' : ''}`} />
          <span className="font-bold text-sm text-text-hi">{ac.id}</span>
          <Tooltip text={GLOSSARY[ac.type]} enabled={tooltipsEnabled}>
            <span className="flex items-center gap-1 text-xs text-text-dim">
              <JetIcon />
              {ac.type}
            </span>
          </Tooltip>
        </div>
        <Tooltip text={GLOSSARY[s.label]} enabled={tooltipsEnabled}>
          <span className={`text-xs font-bold tracking-wider ${s.color}`}>{s.label}</span>
        </Tooltip>
      </div>

      {/* Life bar */}
      <div>
        <div className="flex justify-between text-xs mb-0.5">
          <span className="text-text-dim">Life remaining</span>
          <span className={`font-semibold ${lifeTextColor(ac.remaining_life)}`}>{ac.remaining_life}h</span>
        </div>
        <div className="h-1.5 bg-raised rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${lifeColor(ac.remaining_life)}`}
            style={{ width: `${lifePct}%` }}
          />
        </div>
      </div>

      {/* Flight hours + config row */}
      <div className="flex items-center justify-between text-xs">
        <Tooltip text={GLOSSARY[ac.configuration]} enabled={tooltipsEnabled}>
          <span className="text-text-lo">{ac.configuration}</span>
        </Tooltip>
        <span className="text-text-dim">{ac.total_flight_hours}h total</span>
      </div>

      {/* Config + mission/location */}
      <div className="flex items-center justify-between text-xs">
        <span className="text-text-dim">{ac.location}</span>
        {ac.status === 'on_mission' && mission && (
          <span className="text-col-blue font-semibold">{mission}</span>
        )}
        {ac.maintenance_eta != null && (
          <span className="text-col-amber font-semibold">{ac.maintenance_eta}h ETA</span>
        )}
        {ac.return_eta != null && (
          <span className="text-col-cyan font-semibold">{ac.return_eta}h to base</span>
        )}
      </div>

      {/* Payload */}
      {ac.current_payload?.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {ac.current_payload.map((p, i) => (
            <span key={i} className="px-1.5 py-0.5 bg-raised text-text-dim text-xs rounded">{p}</span>
          ))}
        </div>
      )}

      {/* Fault */}
      {ac.fault && (
        <div className="bg-col-red/10 border border-col-red/30 rounded px-2 py-1 text-xs text-col-red">
          <Tooltip text={Object.entries(GLOSSARY).find(([k]) => ac.fault.includes(k))?.[1]} enabled={tooltipsEnabled}>
            <span>{ac.fault}</span>
          </Tooltip>
        </div>
      )}

      {/* Action buttons */}
      <div className="flex gap-1 pt-0.5">
        {ac.status === 'green' && (
          <button
            onClick={() => {
              if (window.confirm(`Trigger a random fault on ${ac.id}? This will put it into maintenance.`)) {
                onAction('/api/action/trigger-fault', { aircraft_id: ac.id })
              }
            }}
            className="flex-1 py-0.5 text-xs border border-col-red/40 text-col-red hover:bg-col-red/10 rounded transition-colors"
          >
            Trigger Fault
          </button>
        )}
        {ac.status === 'red' && (
          <button
            onClick={() => onAction('/api/action/complete-maintenance', { aircraft_id: ac.id })}
            className="flex-1 py-0.5 text-xs border border-col-green/40 text-col-green hover:bg-col-green/10 rounded transition-colors"
          >
            Complete Maint
          </button>
        )}
        {ac.status === 'on_mission' && (
          <button
            onClick={() => onAction('/api/action/recall-aircraft', { aircraft_id: ac.id })}
            className="flex-1 py-0.5 text-xs border border-col-blue/40 text-col-blue hover:bg-col-blue/10 rounded transition-colors"
          >
            RTB
          </button>
        )}
      </div>
    </div>
  )
}

export default function FleetPanel({ state, onAction, fleetFilter, onClearFilter }) {
  const aircraft = state?.aircraft ?? []

  const missionByAircraft = {}
  ;(state?.ato?.missions ?? []).forEach(m => {
    ;(m.assigned_aircraft ?? []).forEach(id => {
      missionByAircraft[id] = m.id
    })
  })

  const allGroups = [
    { key: 'green',      label: 'Ready' },
    { key: 'on_mission', label: 'Airborne' },
    { key: 'returning',  label: 'Returning' },
    { key: 'red',        label: 'Maintenance' },
    { key: 'grey',       label: 'Cannibalized' },
  ]

  const groups = {
    green:      aircraft.filter(a => a.status === 'green'),
    on_mission: aircraft.filter(a => a.status === 'on_mission'),
    returning:  aircraft.filter(a => a.status === 'returning'),
    red:        aircraft.filter(a => a.status === 'red'),
    grey:       aircraft.filter(a => a.status === 'grey'),
  }

  const visibleGroups = fleetFilter
    ? allGroups.filter(g => g.key === fleetFilter)
    : allGroups.filter(g => groups[g.key].length > 0)

  return (
    <div className="space-y-4">

      {/* Active filter banner */}
      {fleetFilter && (
        <div className="flex items-center justify-between bg-raised border border-border rounded px-3 py-1.5">
          <span className="text-xs text-text-lo">
            Filtered: <span className="text-text-hi font-semibold capitalize">{fleetFilter.replace('_', ' ')}</span>
          </span>
          <button
            onClick={onClearFilter}
            className="text-xs text-text-dim hover:text-text-hi transition-colors"
          >
            Clear filter ×
          </button>
        </div>
      )}

      {/* Wear summary — hidden when filtered */}
      {!fleetFilter && (
        <div className="bg-surface border border-border rounded p-3">
          <div className="text-xs text-text-dim uppercase tracking-wider mb-2">Fleet Wear — hours to heavy service</div>
          <div className="space-y-1.5">
            {[...aircraft].sort((a, b) => a.remaining_life - b.remaining_life).map(ac => (
              <div key={ac.id} className="flex items-center gap-2">
                <span className="text-xs text-text-lo w-10 flex-shrink-0">{ac.id}</span>
                <div className="flex-1 h-2 bg-raised rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${lifeColor(ac.remaining_life)}`}
                    style={{ width: `${Math.min(100, (ac.remaining_life / 200) * 100)}%` }}
                  />
                </div>
                <span className={`text-xs w-12 text-right flex-shrink-0 ${lifeTextColor(ac.remaining_life)}`}>
                  {ac.remaining_life}h
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Aircraft cards grouped by status */}
      {visibleGroups.map(g => (
        <div key={g.key}>
          <div className="text-xs text-text-dim uppercase tracking-wider mb-2">{g.label} ({groups[g.key].length})</div>
          <div className="grid grid-cols-2 gap-2">
            {groups[g.key].map(ac => (
              <AircraftCard
                key={ac.id}
                ac={ac}
                mission={missionByAircraft[ac.id]}
                onAction={onAction}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
