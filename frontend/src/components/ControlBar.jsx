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
        onClick={() => {
          if (window.confirm('Inject a random event? This will mutate the current state.')) {
            onAction('/api/action/random-event')
          }
        }}
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
