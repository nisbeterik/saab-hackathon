function gradeStyle(grade) {
  if (!grade) return 'text-text-dim'
  if (grade.startsWith('Gold'))     return 'text-col-amber'
  if (grade.startsWith('Silver'))   return 'text-col-blue'
  if (grade.startsWith('Bronze'))   return 'text-text-lo'
  if (grade.startsWith('Marginal')) return 'text-col-amber'
  return 'text-col-red'
}

export default function GameOverModal({ state, onReset }) {
  if (!state?.campaign_over) return null

  const victory = state.campaign_result === 'victory'
  const score   = state.campaign_score ?? 0
  const grade   = state.campaign_grade ?? ''
  const reason  = state.campaign_over_reason ?? ''
  const total   = state.missions_total ?? 0
  const done    = state.missions_completed ?? 0
  const lost    = state.aircraft_written_off ?? []
  const successRate = total > 0 ? Math.round((done / total) * 100) : 0

  // Key score decisions
  const scoreLog = state.score_log ?? []
  const topMistakes = scoreLog
    .filter(e => e.category === 'decision' && e.delta < 0)
    .sort((a, b) => a.delta - b.delta)
    .slice(0, 3)

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
      <div className="bg-base border border-border rounded-lg shadow-2xl w-[480px] max-h-[90vh] overflow-y-auto">

        {/* Header */}
        <div className={`px-6 pt-6 pb-4 border-b border-border ${victory ? 'bg-col-green/5' : 'bg-col-red/5'}`}>
          <div className="text-xs uppercase tracking-widest text-text-dim mb-1">
            {victory ? 'Campaign Complete — Day 7 Survived' : 'Campaign Failed'}
          </div>
          <div className={`text-3xl font-bold mb-1 ${victory ? 'text-col-green' : 'text-col-red'}`}>
            {victory ? 'MISSION ACCOMPLISHED' : 'CAMPAIGN OVER'}
          </div>
          <div className="text-sm text-text-dim">{reason}</div>
        </div>

        {/* Stats */}
        <div className="px-6 py-4 grid grid-cols-2 gap-4 border-b border-border">
          <div>
            <div className="text-xs text-text-dim uppercase tracking-wider mb-1">Final Score</div>
            <div className={`text-2xl font-bold ${gradeStyle(grade)}`}>{score}</div>
            <div className={`text-xs font-semibold mt-0.5 ${gradeStyle(grade)}`}>{grade}</div>
          </div>
          <div>
            <div className="text-xs text-text-dim uppercase tracking-wider mb-1">Sortie Record</div>
            <div className="text-2xl font-bold text-text-hi">{successRate}%</div>
            <div className="text-xs text-text-dim">{done}/{total} sorties successful</div>
          </div>
        </div>

        {/* Aircraft lost */}
        {lost.length > 0 && (
          <div className="px-6 py-3 border-b border-border">
            <div className="text-xs text-col-red/70 uppercase tracking-wider mb-2">Aircraft Written Off</div>
            <div className="flex flex-wrap gap-2">
              {lost.map(id => (
                <span key={id} className="px-2 py-1 bg-col-red/10 border border-col-red/30 rounded text-xs text-col-red font-bold line-through">
                  {id}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Key mistakes */}
        {topMistakes.length > 0 && (
          <div className="px-6 py-3 border-b border-border">
            <div className="text-xs text-text-dim uppercase tracking-wider mb-2">Key Decision Points</div>
            <div className="space-y-2">
              {topMistakes.map((e, i) => (
                <div key={i} className="flex items-start gap-2">
                  <span className="text-col-red text-xs font-bold flex-shrink-0 w-8">{e.delta}</span>
                  <div>
                    <div className="text-xs text-text-hi">{e.reason}</div>
                    <div className="text-xs text-text-dim">{e.detail}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Call to action */}
        <div className="px-6 py-4 flex gap-3">
          <button
            onClick={onReset}
            className="flex-1 py-2 rounded text-sm font-semibold border border-col-green/50 text-col-green hover:bg-col-green/10 transition-colors"
          >
            New Campaign
          </button>
          <div className="text-xs text-text-dim self-center">
            Ask the AI: "What went wrong?"
          </div>
        </div>

      </div>
    </div>
  )
}
