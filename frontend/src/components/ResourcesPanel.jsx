const WEAPON_MAX = { 'Robot-1': 20, 'Bomb-2': 16, 'Robot-15': 8 }
const EU_MAX     = { Radar: 4, SignalProcessor: 4, EjectionSeat: 2, HydraulicPump: 4 }
const PERS_MAX   = { klargoring_crew: 6, maintenance_tech: 6, pilots: 12 }
const PERS_LABEL = { klargoring_crew: 'Klargöring', maintenance_tech: 'Maint. Tech', pilots: 'Pilots' }

function statusColor(pct) {
  if (pct > 60) return '#3fb950'
  if (pct > 25) return '#d29922'
  return '#f85149'
}

function StatBar({ label, value, max, unit = '' }) {
  const pct = max > 0 ? Math.min(100, (value / max) * 100) : 0
  const color = statusColor(pct)
  return (
    <div className="flex items-center gap-3">
      <div className="w-28 shrink-0 text-xs text-text-lo truncate">{label}</div>
      <div className="flex-1 h-1.5 bg-raised rounded-full overflow-hidden">
        <div className="h-full rounded-full transition-all duration-500" style={{ width: `${pct}%`, backgroundColor: color }} />
      </div>
      <div className="w-16 text-right text-xs font-mono font-semibold" style={{ color }}>
        {value.toLocaleString()}{unit}
      </div>
    </div>
  )
}

function SectionCard({ title, icon, children }) {
  return (
    <div className="bg-surface border border-border rounded-lg overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-2.5 border-b border-border bg-raised">
        <span className="text-base">{icon}</span>
        <span className="text-xs font-semibold uppercase tracking-widest text-text-lo">{title}</span>
      </div>
      <div className="p-4 space-y-3">
        {children}
      </div>
    </div>
  )
}

function BigStat({ label, value, sub, color = '#e6edf3' }) {
  return (
    <div className="flex flex-col">
      <span className="text-2xl font-bold font-mono" style={{ color }}>{value}</span>
      <span className="text-xs text-text-lo">{label}</span>
      {sub && <span className="text-xs text-text-dim mt-0.5">{sub}</span>}
    </div>
  )
}

export default function ResourcesPanel({ state }) {
  const r = state?.resources
  if (!r) return <div className="text-text-dim text-sm p-4">No resource data.</div>

  const fuelPct    = Math.min(100, (r.fuel / 100000) * 100)
  const fuelColor  = statusColor(fuelPct)
  const sorties    = Math.floor(r.fuel / 4000)
  return (
    <div className="space-y-3">

      {/* Fuel — big hero card */}
      <div className="bg-surface border border-border rounded-lg overflow-hidden">
        <div className="flex items-center gap-2 px-4 py-2.5 border-b border-border bg-raised">
          <span className="text-base">⛽</span>
          <span className="text-xs font-semibold uppercase tracking-widest text-text-lo">Fuel</span>
        </div>
        <div className="p-4">
          <div className="flex items-end justify-between mb-3">
            <BigStat
              label="Liters available"
              value={r.fuel.toLocaleString()}
              sub={`${sorties} sorties remaining`}
              color={fuelColor}
            />
            <div className="text-right">
              <span className="text-2xl font-bold font-mono" style={{ color: fuelColor }}>
                {fuelPct.toFixed(0)}%
              </span>
              <div className="text-xs text-text-dim">of capacity</div>
            </div>
          </div>
          {/* Segmented fuel bar */}
          <div className="h-3 bg-raised rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{ width: `${fuelPct}%`, backgroundColor: fuelColor }}
            />
          </div>
          <div className="flex justify-between text-xs text-text-dim mt-1.5">
            <span>0</span>
            <span>25k</span>
            <span>50k</span>
            <span>75k</span>
            <span>100k L</span>
          </div>
        </div>
      </div>

      {/* Weapons */}
      <SectionCard title="Weapons" icon="🚀">
        {Object.entries(r.weapons ?? {}).map(([k, v]) => (
          <StatBar key={k} label={k} value={v} max={WEAPON_MAX[k] ?? Math.max(v * 2, 4)} unit=" rds" />
        ))}
        {Object.keys(r.weapons ?? {}).length === 0 && (
          <div className="text-xs text-red-400 font-semibold">⚠ No weapons on hand</div>
        )}
      </SectionCard>

      {/* Exchange Units */}
      <SectionCard title="Exchange Units (UE)" icon="🔧">
        <div className="grid grid-cols-2 gap-x-6 gap-y-3">
          {Object.entries(r.exchange_units ?? {}).map(([k, v]) => {
            const max = EU_MAX[k] ?? Math.max(v + 2, 4)
            const pct = Math.min(100, (v / max) * 100)
            const color = statusColor(pct)
            return (
              <div key={k} className="flex flex-col gap-1">
                <div className="flex justify-between items-baseline">
                  <span className="text-xs text-text-lo truncate">{k}</span>
                  <span className="text-xs font-mono font-bold ml-2" style={{ color }}>{v}</span>
                </div>
                <div className="h-1 bg-raised rounded-full overflow-hidden">
                  <div className="h-full rounded-full" style={{ width: `${pct}%`, backgroundColor: color }} />
                </div>
              </div>
            )
          })}
        </div>
      </SectionCard>

      {/* Personnel */}
      <SectionCard title="Personnel" icon="👥">
        <div className="grid grid-cols-3 gap-3">
          {Object.entries(r.personnel ?? {}).map(([k, v]) => {
            const max = PERS_MAX[k] ?? Math.max(v + 2, 6)
            const pct = Math.min(100, (v / max) * 100)
            const color = statusColor(pct)
            return (
              <div key={k} className="bg-raised rounded p-3 flex flex-col items-center gap-1 border border-border">
                <span className="text-2xl font-bold font-mono" style={{ color }}>{v}</span>
                <span className="text-xs text-text-dim text-center leading-tight">{PERS_LABEL[k] ?? k}</span>
                <div className="w-full h-1 bg-bg-base rounded-full overflow-hidden mt-1">
                  <div className="h-full rounded-full" style={{ width: `${pct}%`, backgroundColor: color }} />
                </div>
              </div>
            )
          })}
        </div>
      </SectionCard>

      {/* Spare Parts */}
      <SectionCard title="Spare Parts" icon="📦">
        <StatBar label="Generic spares" value={r.spare_parts} max={50} unit=" units" />
        <div className="text-xs text-text-dim">
          Pool covers minor LRU swaps · critical parts tracked as Exchange Units above
        </div>
      </SectionCard>

    </div>
  )
}
