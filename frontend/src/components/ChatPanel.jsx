import { useEffect, useRef, useState } from 'react'

const QUICK_PROMPTS = [
  'Which aircraft should I assign to the next unassigned mission?',
  "QRA isn't manned — what's the risk if I leave it empty?",
  'Should I request a resupply convoy now or wait?',
  'One of my aircraft is below 20h life — should I fly it or ground it?',
]

function fmtTime(date) {
  if (!date) return ''
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })
}

// Pixel-art Ozzy Osbourne mascot
function Mascot({ talking = false }) {
  const s = 3
  const T = null
  // Palette
  const HR = '#2a1a0e'  // dark brown/black hair
  const SK = '#d4b896'  // pale skin
  const EY = '#1a0800'  // dark pupils
  const GL = '#6b1a5e'  // purple tinted glasses frame
  const GL2= '#8b2a7a'  // glasses lens highlight
  const CT = '#5a0d2a'  // dark maroon coat
  const CD = '#3d0820'  // coat shadow/lapel
  const SH = '#4a3a8a'  // purple shirt
  const CR = '#b8960c'  // gold cross
  const MR = '#7a1f1f'  // mouth interior red
  const MH = '#c8a882'  // mouth edge skin

  // 12 wide × 19 tall
  const grid = [
    [T,  HR, HR, HR, HR, HR, HR, HR, HR, HR, HR, T ],  // hair top
    [HR, HR, HR, HR, HR, HR, HR, HR, HR, HR, HR, HR],  // hair wide
    [HR, HR, SK, SK, SK, SK, SK, SK, SK, SK, HR, HR],  // forehead + hair sides
    [HR, SK, SK, SK, SK, SK, SK, SK, SK, SK, SK, HR],  // face
    [HR, SK, GL, GL, SK, SK, SK, GL, GL, SK, SK, HR],  // glasses row 1 (frames)
    [HR, SK, GL, GL2,SK, SK, SK, GL, GL2,SK, SK, HR],  // glasses row 2 (lenses)
    [HR, SK, GL, GL, SK, SK, SK, GL, GL, SK, SK, HR],  // glasses row 3 (frames)
    [HR, SK, SK, SK, SK, SK, SK, SK, SK, SK, SK, HR],  // nose area
    [HR, SK, SK, SK, SK, SK, SK, SK, SK, SK, SK, HR],  // mouth row (overlaid)
    [HR, HR, SK, SK, SK, SK, SK, SK, SK, SK, HR, HR],  // chin
    [T,  HR, HR, SK, SK, SK, SK, SK, SK, HR, HR, T ],  // jaw + hair drape
    [T,  CD, CD, CD, SH, SH, SH, SH, CD, CD, CD, T ],  // collar / lapels
    [T,  CT, CD, SH, SH, CR, SH, SH, CD, CT, CT, T ],  // coat + cross
    [T,  CT, CT, SH, SH, CR, SH, SH, CT, CT, CT, T ],  // cross middle
    [T,  CT, CT, SH, SH, SH, SH, SH, CT, CT, CT, T ],  // shirt lower
    [T,  CT, CT, CT, CT, CT, CT, CT, CT, CT, CT, T ],  // coat body
    [T,  CT, CT, CT, CT, CT, CT, CT, CT, CT, CT, T ],  // coat body
    [T,  CT, CT, CT, CT, CT, CT, CT, CT, CT, CT, T ],  // coat lower
    [T,  T,  CT, CT, CT, CT, CT, CT, CT, CT, T,  T ],  // coat hem
  ]

  return (
    <svg
      width={12 * s} height={19 * s}
      style={{ imageRendering: 'pixelated', flexShrink: 0 }}
      aria-hidden="true"
    >
      {grid.flatMap((row, ri) =>
        row.map((color, ci) =>
          color ? <rect key={`${ri}-${ci}`} x={ci * s} y={ri * s} width={s} height={s} fill={color} /> : null
        )
      )}
      {/* Mouth — closed: thin dark line */}
      <rect
        x={4 * s} y={8 * s + 1} width={4 * s} height={1} fill={EY}
        className={talking ? 'mouth-closed-talking' : ''}
      />
      {/* Mouth — open: red interior */}
      <rect
        x={4 * s} y={8 * s} width={4 * s} height={s + 2} fill={MR}
        className={talking ? 'mouth-open-talking' : ''}
        opacity={talking ? undefined : 0}
      />
      {/* Mouth corners when open */}
      <rect
        x={3 * s + 1} y={8 * s + 1} width={s - 1} height={s} fill={MH}
        className={talking ? 'mouth-open-talking' : ''}
        opacity={talking ? undefined : 0}
      />
      <rect
        x={8 * s} y={8 * s + 1} width={s - 1} height={s} fill={MH}
        className={talking ? 'mouth-open-talking' : ''}
        opacity={talking ? undefined : 0}
      />
    </svg>
  )
}

// Left-pointing speech bubble tail (border + fill layers)
function BubbleTail() {
  return (
    <>
      <div className="absolute top-3" style={{ left: -7, width: 0, height: 0,
        borderTop: '5px solid transparent', borderBottom: '5px solid transparent',
        borderRight: '7px solid #30363d' }} />
      <div className="absolute top-3" style={{ left: -5, width: 0, height: 0,
        borderTop: '5px solid transparent', borderBottom: '5px solid transparent',
        borderRight: '6px solid #1c2128' }} />
    </>
  )
}

// Render a single line with **bold** and *italic* segments
function renderLine(line, key) {
  const parts = line.split(/(\*\*[^*]+\*\*|\*[^*]+\*)/g)
  return (
    <span key={key}>
      {parts.map((part, i) => {
        if (part.startsWith('**') && part.endsWith('**'))
          return <strong key={i} className="font-semibold text-text-hi">{part.slice(2, -2)}</strong>
        if (part.startsWith('*') && part.endsWith('*'))
          return <em key={i} className="italic text-text-lo">{part.slice(1, -1)}</em>
        return part
      })}
    </span>
  )
}

// Render content with **bold** and newlines preserved
function RichContent({ text }) {
  const lines = text.split('\n')
  return (
    <div className="whitespace-pre-wrap">
      {lines.map((line, i) => (
        <span key={i}>
          {renderLine(line, i)}
          {i < lines.length - 1 && '\n'}
        </span>
      ))}
    </div>
  )
}

function Message({ msg }) {
  const isUser = msg.role === 'user'

  if (isUser) {
    return (
      <div className="flex flex-col items-end">
        <div className="max-w-[85%] rounded px-3 py-2 text-xs leading-relaxed bg-col-blue/20 border border-col-blue/40 text-text-hi">
          <RichContent text={msg.content} />
        </div>
        {msg.time && <div className="text-xs text-text-dim mt-0.5 px-1">{fmtTime(msg.time)}</div>}
      </div>
    )
  }

  return (
    <div className="flex flex-col items-start">
      <div className="flex items-end gap-2">
        <Mascot talking={false} />
        <div className="relative max-w-[80%]">
          <BubbleTail />
          <div className="bg-raised border border-border rounded px-3 py-2 text-xs leading-relaxed text-text-hi">
            <RichContent text={msg.content} />
          </div>
        </div>
      </div>
      {msg.time && <div className="text-xs text-text-dim mt-0.5 ml-10 px-1">{fmtTime(msg.time)}</div>}
    </div>
  )
}

export default function ChatPanel({
  messages, input, loading, onInputChange, onSend, onClear,
}) {
  const bottomRef = useRef(null)
  const textareaRef = useRef(null)
  const [showSuggestions, setShowSuggestions] = useState(false)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  useEffect(() => {
    const ta = textareaRef.current
    if (!ta) return
    ta.style.height = 'auto'
    ta.style.height = `${Math.min(ta.scrollHeight, 160)}px`
  }, [input])

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      onSend()
    }
  }

  const pickPrompt = (q) => {
    onInputChange(q)
    setShowSuggestions(false)
  }

  return (
    <div className="flex flex-col h-full relative">

      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-border flex-shrink-0">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-col-green" />
          <span className="text-xs font-bold tracking-wider uppercase text-text-hi">Ozzy Ai-rborne</span>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setShowSuggestions(s => !s)}
            className={`text-xs px-2 py-0.5 rounded border transition-colors
              ${showSuggestions
                ? 'border-col-blue/50 text-col-blue bg-col-blue/10'
                : 'border-transparent text-text-dim hover:text-text-lo hover:bg-raised'
              }`}
          >
            Prompts
          </button>
          <button
            onClick={onClear}
            className="text-xs text-text-dim hover:text-text-lo transition-colors px-2 py-0.5 rounded hover:bg-raised"
          >
            Clear
          </button>
        </div>
      </div>

      {/* Quick suggestions dropdown */}
      {showSuggestions && (
        <div className="absolute top-10 left-0 right-0 z-10 bg-raised border-b border-border p-2 space-y-1 shadow-lg">
          {QUICK_PROMPTS.map((q, i) => (
            <button
              key={i}
              onClick={() => pickPrompt(q)}
              className="w-full text-left text-xs text-text-lo hover:text-text-hi px-2 py-1.5 rounded hover:bg-surface border border-transparent hover:border-border transition-colors"
            >
              {q}
            </button>
          ))}
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {messages.length === 0 && (
          <div className="space-y-2 text-xs text-text-dim">
            <p className="font-semibold text-text-lo">Based Commander AI — Ask anything:</p>
            <ul className="space-y-1 list-none">
              {QUICK_PROMPTS.map((q, i) => (
                <li
                  key={i}
                  className="cursor-pointer hover:text-text-hi transition-colors px-2 py-1 rounded hover:bg-raised border border-transparent hover:border-border"
                  onClick={() => onInputChange(q)}
                >
                  "{q}"
                </li>
              ))}
            </ul>
          </div>
        )}
        {messages.map((msg, i) => <Message key={i} msg={msg} />)}
        {loading && (
          <div className="flex items-end gap-2">
            <Mascot talking={true} />
            <div className="relative">
              <BubbleTail />
              <div className="bg-raised border border-border rounded px-3 py-2">
                <div className="flex gap-1">
                  {[0, 1, 2].map(i => (
                    <span
                      key={i}
                      className="w-1.5 h-1.5 bg-text-dim rounded-full animate-bounce"
                      style={{ animationDelay: `${i * 0.15}s` }}
                    />
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="flex-shrink-0 border-t border-border p-2">
        <div className="flex gap-2">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={e => onInputChange(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Ask the AI commander..."
            className="flex-1 bg-raised border border-border rounded px-2 py-1.5 text-xs text-text-hi
              placeholder-text-dim resize-none focus:outline-none focus:border-col-blue transition-colors
              min-h-[3rem] max-h-[160px]"
          />
          <button
            onClick={onSend}
            disabled={!input.trim() || loading}
            className="px-3 py-1 bg-col-blue text-white text-xs font-bold rounded
              hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed transition-colors self-end"
          >
            Send
          </button>
        </div>
        <div className="text-xs text-text-dim mt-1 px-0.5">Enter to send · Shift+Enter for newline</div>
      </div>
    </div>
  )
}
