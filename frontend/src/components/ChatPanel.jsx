import { useEffect, useRef, useState } from 'react'

const QUICK_PROMPTS = [
  'Which aircraft for the next DCA sortie?',
  "What's our readiness for the next 48h?",
  "GE05 failed BIT — complex LRU fault. What's the impact?",
  'Should I use a Radar UE on GE05 or hold it in reserve?',
]

function fmtTime(date) {
  if (!date) return ''
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })
}

function Message({ msg }) {
  const isUser = msg.role === 'user'
  return (
    <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
      <div
        className={`max-w-[85%] rounded px-3 py-2 text-xs leading-relaxed
          ${isUser
            ? 'bg-col-blue/20 border border-col-blue/40 text-text-hi'
            : 'bg-raised border border-border text-text-hi'
          }`}
      >
        <div className="whitespace-pre-wrap">{msg.content}</div>
      </div>
      {msg.time && (
        <div className="text-xs text-text-dim mt-0.5 px-1">{fmtTime(msg.time)}</div>
      )}
    </div>
  )
}

export default function ChatPanel({
  messages, input, loading, onInputChange, onSend, onClear,
  scenarios = [], onRunScenario, actionLoading = false,
}) {
  const bottomRef = useRef(null)
  const textareaRef = useRef(null)
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [showScript, setShowScript] = useState(false)

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

  const loadScenario = (label) => {
    setShowScript(false)
    onRunScenario(label)
  }

  return (
    <div className="flex flex-col h-full relative">

      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-border flex-shrink-0">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-col-green" />
          <span className="text-xs font-bold tracking-wider uppercase text-text-hi">AI Assistant</span>
        </div>
        <div className="flex items-center gap-1">
          {scenarios.length > 0 && (
            <button
              onClick={() => { setShowScript(s => !s); setShowSuggestions(false) }}
              title="Demo script — pre-scripted steps that load a situation and pre-fill the chat. ⚡ steps also trigger a state event."
              className={`text-xs px-2 py-0.5 rounded border transition-colors
                ${showScript
                  ? 'border-col-amber/50 text-col-amber bg-col-amber/10'
                  : 'border-transparent text-text-dim hover:text-text-lo hover:bg-raised'
                }`}
            >
              Script
            </button>
          )}
          <button
            onClick={() => { setShowSuggestions(s => !s); setShowScript(false) }}
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

      {/* Demo script dropdown */}
      {showScript && (
        <div className="absolute top-10 left-0 right-0 z-10 bg-raised border-b border-border p-2 space-y-1 shadow-lg max-h-72 overflow-y-auto">
          <div className="text-xs text-text-dim uppercase tracking-wider px-1 pb-1">
            Demo Script — click a step to load
          </div>
          {scenarios.map((s, i) => (
            <button
              key={s.label}
              onClick={() => loadScenario(s.label)}
              disabled={actionLoading}
              className="w-full text-left text-xs px-2 py-1.5 rounded hover:bg-surface border border-transparent
                hover:border-border transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <span className="text-text-dim mr-1.5 font-mono">{String(i + 1).padStart(2, '0')}.</span>
              <span className="text-text-hi">{s.label}</span>
              {s.has_event && (
                <span className="ml-1.5 text-col-amber" title="Triggers a state mutation">⚡</span>
              )}
            </button>
          ))}
        </div>
      )}

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
            <p className="font-semibold text-text-lo">Base Commander AI — Ask anything:</p>
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
          <div className="flex justify-start">
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
