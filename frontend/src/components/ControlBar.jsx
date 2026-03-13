const SCENARIOS = [
  {
    label: 'New ATO',
    sub:   'Allocate fleet',
    path:  '/api/scenario/1',
    color: 'border-col-blue text-col-blue hover:bg-col-blue/10',
  },
  {
    label: 'BIT Fault',
    sub:   'GE05 + cascade',
    path:  '/api/scenario/2',
    color: 'border-col-red text-col-red hover:bg-col-red/10',
  },
  {
    label: 'Advance 6h',
    sub:   'Time skip',
    path:  '/api/scenario/3',
    color: 'border-col-amber text-col-amber hover:bg-col-amber/10',
  },
]

const TIME_ACTIONS = [
  { label: '+1h',  hours: 1  },
  { label: '+6h',  hours: 6  },
  { label: '+12h', hours: 12 },
]

export default function ControlBar({ onAction, loading }) {
  const handleReset = () => {
    if (window.confirm('Reset all state to initial? This cannot be undone.')) {
      onAction('/api/action/reset')
    }
  }

  return (
    <div className="flex flex-wrap items-center gap-2">

      {/* Scenario buttons */}
      <div className="flex gap-1.5">
        {SCENARIOS.map(s => (
          <button
            key={s.path}
            onClick={() => onAction(s.path)}
            disabled={loading}
            className={`flex flex-col items-center px-3 py-1 border rounded text-xs font-semibold
              transition-colors disabled:opacity-40 disabled:cursor-not-allowed ${s.color}`}
          >
            <span>{s.label}</span>
            <span className="text-xs opacity-70 font-normal">{s.sub}</span>
          </button>
        ))}
      </div>

      <div className="w-px h-8 bg-border" />

      {/* Time controls */}
      <div className="flex gap-1">
        {TIME_ACTIONS.map(t => (
          <button
            key={t.label}
            onClick={() => onAction('/api/action/advance-time', { hours: t.hours })}
            disabled={loading}
            className="px-2.5 py-1 border border-border text-text-lo hover:text-text-hi hover:border-text-dim
              rounded text-xs font-semibold transition-colors disabled:opacity-40"
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="w-px h-8 bg-border" />

      {/* Random event */}
      <button
        onClick={() => onAction('/api/action/random-event')}
        disabled={loading}
        className="px-3 py-1 border border-col-amber/50 text-col-amber hover:bg-col-amber/10
          rounded text-xs font-semibold transition-colors disabled:opacity-40"
      >
        Random Event
      </button>

      {loading && (
        <span className="text-xs text-text-dim animate-pulse">Processing...</span>
      )}

      {/* Reset — right-aligned, guarded by confirm */}
      <div className="ml-auto">
        <button
          onClick={handleReset}
          disabled={loading}
          className="px-3 py-1 border border-border text-text-dim hover:text-col-red hover:border-col-red/50
            rounded text-xs font-semibold transition-colors disabled:opacity-40"
        >
          Reset
        </button>
      </div>
    </div>
  )
}
