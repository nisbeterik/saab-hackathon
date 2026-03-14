import { useState, useRef } from 'react'

export default function Tooltip({ children, text, enabled }) {
  if (!enabled || !text) return <>{children}</>
  const [pos, setPos] = useState(null)
  const ref = useRef(null)

  return (
    <span
      ref={ref}
      className="inline-block"
      onMouseEnter={() => {
        if (!ref.current) return
        const r = ref.current.getBoundingClientRect()
        setPos({
          bottom: window.innerHeight - r.top + 6,
          left: Math.min(r.left, window.innerWidth - 240),
        })
      }}
      onMouseLeave={() => setPos(null)}
    >
      {children}
      {pos && (
        <span
          className="pointer-events-none fixed z-[9999] w-max max-w-56 px-2 py-1 rounded
            bg-[#161b22] border border-border text-xs text-text-hi shadow-lg
            whitespace-normal text-left leading-snug font-normal"
          style={{ bottom: `${pos.bottom}px`, left: `${Math.max(4, pos.left)}px` }}
        >
          {text}
        </span>
      )}
    </span>
  )
}
