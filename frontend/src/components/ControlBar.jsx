import { useContext } from 'react'
import { TooltipCtx } from '../App'
import Tooltip from './Tooltip'

const TIME_ACTIONS = [
  { label: '+1h',  hours: 1  },
  { label: '+6h',  hours: 6  },
  { label: '+12h', hours: 12 },
]

const SCENARIO_COLORS = [
  'border-col-blue  text-col-blue  hover:bg-col-blue/10',
  'border-col-red   text-col-red   hover:bg-col-red/10',
  'border-col-amber text-col-amber hover:bg-col-amber/10',
]

export default function ControlBar({
  onAction, loading, scenarios = [], onRunScenario,
  autoplay, onToggleAutoplay,
  autoplaySpeedIdx, onCycleSpeed, autoplaySpeeds = [],
  autoplayRandomEvents, onToggleRandomEvents,
}) {
  const tooltipsEnabled = useContext(TooltipCtx)
  const handleReset = () => {
    if (window.confirm('Reset all state to initial? This cannot be undone.')) {
      onAction('/api/action/reset')
    }
  }

  const speedEntry = autoplaySpeeds[autoplaySpeedIdx] ?? { label: '×1 Slow', tip: '' }

  return (
    <div className="flex flex-wrap items-center gap-2">

      {/* Scenario buttons */}
      {scenarios.length > 0 && (
        <>
          <Tooltip
            text="Pre-scripted demo steps — each loads a situation and pre-fills the chat with a question. ⚡ steps also trigger a state event."
            enabled={tooltipsEnabled}
          >
            <span className="text-[10px] font-bold tracking-wider uppercase text-text-dim cursor-default select-none">
              Scenarios
            </span>
          </Tooltip>
          <div className="flex gap-1.5">
            {scenarios.map((s, i) => (
              <button
                key={s.label}
                onClick={() => onRunScenario(s.label)}
                disabled={loading}
                title={s.label}
                className={`px-3 py-1 border rounded text-xs font-semibold whitespace-nowrap
                  transition-colors disabled:opacity-40 disabled:cursor-not-allowed
                  ${SCENARIO_COLORS[i % SCENARIO_COLORS.length]}`}
              >
                {s.label.replace(/^\d+\.\s*/, '').split(' — ')[0]}
                {s.has_event && <span className="ml-1 text-col-amber">⚡</span>}
              </button>
            ))}
          </div>
          <div className="w-px h-8 bg-border" />
        </>
      )}

      {/* Autoplay controls */}
      <button
        onClick={onToggleAutoplay}
        disabled={loading}
        className={`px-2.5 py-1 rounded text-xs font-semibold border transition-colors disabled:opacity-40
          ${autoplay
            ? 'border-col-amber/60 text-col-amber hover:bg-col-amber/10'
            : 'border-col-green/60 text-col-green hover:bg-col-green/10'}`}
      >
        {autoplay ? '⏸ Pause' : '▶ Play'}
      </button>

      <Tooltip text={speedEntry.tip} enabled={tooltipsEnabled}>
        <button
          onClick={onCycleSpeed}
          className="px-2.5 py-1 rounded text-xs border border-border text-text-lo hover:text-text-hi transition-colors"
        >
          {speedEntry.label}
        </button>
      </Tooltip>

      <button
        onClick={onToggleRandomEvents}
        title="Occasionally fires random events (BIT faults, weather, new missions) during autoplay — ~4% chance per game-hour"
        className={`px-2.5 py-1 rounded text-xs border transition-colors
          ${autoplayRandomEvents
            ? 'border-col-red/50 text-col-red hover:bg-col-red/10'
            : 'border-border text-text-dim hover:text-text-lo'}`}
      >
        {autoplayRandomEvents ? '🎲 Events ON' : '🎲 Events OFF'}
      </button>

      <div className="w-px h-8 bg-border" />

      {/* Time controls — disabled while autoplay is running */}
      <div className="flex gap-1">
        {TIME_ACTIONS.map(t => (
          <button
            key={t.label}
            onClick={() => onAction('/api/action/advance-time', { hours: t.hours })}
            disabled={loading || autoplay}
            className="px-2.5 py-1 border border-border text-text-lo hover:text-text-hi hover:border-text-dim
              rounded text-xs font-semibold transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
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
