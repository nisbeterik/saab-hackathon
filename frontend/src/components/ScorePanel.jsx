const CATEGORY_COLOR = {
  decision: 'text-col-red',
  luck:     'text-col-amber',
  mixed:    'text-text-lo',
}

const CATEGORY_LABEL = {
  decision: 'YOUR CALL',
  luck:     'BAD LUCK',
  mixed:    'MIXED',
}

function gradeColor(score) {
  if (score >= 750) return 'text-col-green'
  if (score >= 600) return 'text-col-amber'
  if (score >= 400) return 'text-col-red'
  return 'text-col-red animate-pulse'
}

export default function ScorePanel({ state }) {
  const score     = state.campaign_score ?? 1000
  const grade     = state.campaign_grade ?? 'Gold — Outstanding'
  const scoreLog  = state.score_log ?? []
  const total     = state.missions_total ?? 0
  const completed = state.missions_completed ?? 0
  const writtenOff = state.aircraft_written_off ?? []
  const day       = state.current_day ?? 1

  const successRate = total > 0 ? Math.round((completed / total) * 100) : null

  // Split score log by category for totals
  const decisionLoss = scoreLog.filter(e => e.category === 'decision' && e.delta < 0).reduce((s, e) => s + e.delta, 0)
  const luckLoss     = scoreLog.filter(e => e.category === 'luck'     && e.delta < 0).reduce((s, e) => s + e.delta, 0)
  const gains        = scoreLog.filter(e => e.delta > 0).reduce((s, e) => s + e.delta, 0)

  return (
    <div className="space-y-4">

      {/* Summary card */}
      <div className="bg-surface border border-border rounded p-4">
        <div className="flex items-start justify-between mb-3">
          <div>
            <div className="text-xs text-text-dim uppercase tracking-wider mb-1">Commander Rating</div>
            <div className={`text-2xl font-bold ${gradeColor(score)}`}>{score}</div>
            <div className={`text-sm font-semibold mt-0.5 ${gradeColor(score)}`}>{grade}</div>
          </div>
          <div className="text-right">
            <div className="text-xs text-text-dim uppercase tracking-wider mb-1">Campaign Progress</div>
            <div className="text-xl font-bold text-text-hi">Day {day}<span className="text-text-dim text-sm">/7</span></div>
            {writtenOff.length > 0 && (
              <div className="text-xs text-col-red/80 mt-0.5">{writtenOff.length} aircraft lost</div>
            )}
          </div>
        </div>

        {/* Score bar */}
        <div className="h-2 bg-raised rounded-full overflow-hidden mb-3">
          <div
            className={`h-full rounded-full transition-all ${gradeColor(score).replace('text-', 'bg-').replace(' animate-pulse', '')}`}
            style={{ width: `${Math.min(100, Math.max(0, (score / 1200) * 100))}%` }}
          />
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-3 gap-3 text-center">
          <div>
            <div className="text-xs text-text-dim mb-0.5">Sorties flown</div>
            <div className="text-sm font-bold text-text-hi">{total}</div>
          </div>
          <div>
            <div className="text-xs text-text-dim mb-0.5">Success rate</div>
            <div className={`text-sm font-bold ${successRate == null ? 'text-text-dim' : successRate >= 70 ? 'text-col-green' : successRate >= 50 ? 'text-col-amber' : 'text-col-red'}`}>
              {successRate != null ? `${successRate}%` : '—'}
            </div>
          </div>
          <div>
            <div className="text-xs text-text-dim mb-0.5">Score breakdown</div>
            <div className="text-xs">
              <span className="text-col-green">+{gains}</span>
              {' / '}
              <span className="text-col-red">{decisionLoss}</span>
              {' / '}
              <span className="text-col-amber">{luckLoss}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Written-off aircraft */}
      {writtenOff.length > 0 && (
        <div className="bg-col-red/5 border border-col-red/30 rounded p-3">
          <div className="text-xs text-col-red/80 uppercase tracking-wider mb-2">Aircraft Written Off</div>
          <div className="flex flex-wrap gap-2">
            {writtenOff.map(id => (
              <span key={id} className="px-2 py-1 bg-col-red/10 border border-col-red/30 rounded text-xs text-col-red font-bold line-through">
                {id}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Score event log */}
      <div className="bg-surface border border-border rounded">
        <div className="px-3 py-2 border-b border-border flex items-center justify-between">
          <span className="text-xs text-text-dim uppercase tracking-wider">Score Log</span>
          <div className="flex gap-3 text-xs">
            <span className="text-col-red">■ Your call</span>
            <span className="text-col-amber">■ Bad luck</span>
            <span className="text-text-dim">■ Mixed</span>
          </div>
        </div>
        <div className="divide-y divide-border max-h-80 overflow-y-auto">
          {scoreLog.length === 0 && (
            <div className="px-3 py-4 text-xs text-text-dim text-center">No score events yet.</div>
          )}
          {[...scoreLog].reverse().map((e, i) => (
            <div key={i} className="px-3 py-2 flex items-start gap-3">
              <div className="flex-shrink-0 text-xs text-text-dim w-14">
                D{e.day} {String(e.hour).padStart(2, '0')}:00
              </div>
              <div className={`flex-shrink-0 text-xs font-bold w-16 ${CATEGORY_COLOR[e.category] ?? 'text-text-dim'}`}>
                {CATEGORY_LABEL[e.category] ?? e.category}
              </div>
              <div className={`flex-shrink-0 text-xs font-bold w-10 ${e.delta >= 0 ? 'text-col-green' : 'text-col-red'}`}>
                {e.delta >= 0 ? `+${e.delta}` : e.delta}
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-xs text-text-hi truncate">{e.reason}</div>
                <div className="text-xs text-text-dim mt-0.5 leading-relaxed">{e.detail}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Defeat thresholds reminder */}
      <div className="bg-surface border border-border rounded p-3 text-xs space-y-1 text-text-dim">
        <div className="text-text-lo uppercase tracking-wider mb-1.5">Defeat Conditions</div>
        <div className={score < 400 ? 'text-col-red font-semibold' : ''}>Score below 400 → Campaign failed</div>
        <div className={writtenOff.length >= 4 ? 'text-col-red font-semibold' : ''}>4+ aircraft written off → Strategic defeat</div>
        <div>Fleet &lt; 3 operational for 6+ hours → Collapse</div>
      </div>

    </div>
  )
}
