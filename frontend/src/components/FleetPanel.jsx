const STATUS_CONFIG = {
  green:      { label: 'READY',    color: 'text-col-green', dot: 'bg-col-green', border: 'border-col-green/30' },
  red:        { label: 'MAINT',    color: 'text-col-red',   dot: 'bg-col-red',   border: 'border-col-red/30'   },
  grey:       { label: 'GREY',     color: 'text-text-dim',  dot: 'bg-text-dim',  border: 'border-border'        },
  on_mission: { label: 'AIRBORNE', color: 'text-col-blue',  dot: 'bg-col-blue',  border: 'border-col-blue/30'  },
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
  const lifePct = Math.min(100, Math.round((ac.remaining_life / 200) * 100))

  return (
    <div className={`bg-surface border ${s.border} rounded p-3 flex flex-col gap-1.5`}>
      {/* Header row */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full flex-shrink-0 ${s.dot} ${ac.status === 'on_mission' ? 'pulse-dot' : ''}`} />
          <span className="font-bold text-sm text-text-hi">{ac.id}</span>
          <span className="text-xs text-text-dim">{ac.type}</span>
        </div>
        <span className={`text-xs font-bold tracking-wider ${s.color}`}>{s.label}</span>
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
        <span className="text-text-lo">{ac.configuration}</span>
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
          {ac.fault}
        </div>
      )}

      {/* Action buttons */}
      <div className="flex gap-1 pt-0.5">
        {ac.status === 'green' && (
          <button
            onClick={() => onAction('/api/action/trigger-fault', { aircraft_id: ac.id })}
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
            onClick={() => onAction('/api/action/return-from-mission', { aircraft_id: ac.id })}
            className="flex-1 py-0.5 text-xs border border-col-blue/40 text-col-blue hover:bg-col-blue/10 rounded transition-colors"
          >
            Return
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
    { key: 'red',        label: 'Maintenance' },
    { key: 'grey',       label: 'Cannibalized' },
  ]

  const groups = {
    green:      aircraft.filter(a => a.status === 'green'),
    on_mission: aircraft.filter(a => a.status === 'on_mission'),
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
