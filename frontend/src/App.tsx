import { useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import './App.css'

type Message = {
  id: number
  role: 'assistant' | 'user'
  text: string
}

type Product = {
  id: string
  name: string
  category: string
  price: string
  image: string | null
  note: string
  url?: string
  in_stock?: boolean
  stock_level?: string
}

type ChatResponse = {
  assistant_name?: string
  reply: string
  products?: Product[]
  search_query?: string
  city?: string | null
  delivery_date?: string | null
  intent_label?: string
  tone?: string
  friend_note?: string
  next_actions?: string[]
  resources?: CareResource[]
  safety_level?: string
  suppress_products?: boolean
}

type AgentState = {
  assistantName: string
  intentLabel: string
  tone: string
  friendNote: string
  nextActions: string[]
  resources: CareResource[]
  safetyLevel: string | null
  suppressProducts: boolean
}

type CareResource = {
  name: string
  detail: string
  contact: string
}

const defaultAgentState: AgentState = {
  assistantName: 'Kavi',
  intentLabel: 'Close friend shopping',
  tone: 'warm, practical, Sri Lankan',
  friendNote:
    'Kavi reads the situation first, then shops. The goal is useful advice plus real Kapruka products.',
  nextActions: [
    'Tell Kavi the item or situation',
    'Add city, budget, and date',
    'Compare real Kapruka picks',
  ],
  resources: [],
  safetyLevel: null,
  suppressProducts: false,
}

const initialMessages: Message[] = [
  {
    id: 1,
    role: 'assistant',
    text:
      'Ayubowan, I am Kavi. Tell me what happened or what you need to buy. I will think like a close friend first, then help you pick the right Kapruka products.',
  },
]

const starterProducts: Product[] = [
  {
    id: 'starter-flowers',
    name: 'Relationship repair flower plan',
    category: 'Friend mode',
    price: 'Real prices after search',
    image:
      'https://images.unsplash.com/photo-1518709779341-56cf4535e94b?auto=format&fit=crop&w=700&q=80',
    note: 'For apology, comfort, birthday, anniversary, and thoughtful conversations.',
  },
  {
    id: 'starter-grocery',
    name: 'Everyday essentials run',
    category: 'Self shopping',
    price: 'Real prices after search',
    image:
      'https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&w=700&q=80',
    note: 'For groceries, home needs, daily essentials, and practical multi-item carts.',
  },
  {
    id: 'starter-cake',
    name: 'Birthday rescue plan',
    category: 'Gift mode',
    price: 'Real prices after search',
    image:
      'https://images.unsplash.com/photo-1578985545062-69928b1d9587?auto=format&fit=crop&w=700&q=80',
    note: 'For last-minute cakes, flowers, notes, and delivery timing.',
  },
]

const quickPrompts = [
  'I need to break up with my girl, help me',
  'I broke up and need flowers today in Colombo',
  'I need groceries delivered to Colombo tomorrow',
  'Find a birthday gift under Rs. 10000 to Kandy tomorrow',
]

function App() {
  const [messages, setMessages] = useState<Message[]>(initialMessages)
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [products, setProducts] = useState<Product[]>(starterProducts)
  const [searchContext, setSearchContext] = useState('Ready to search Kapruka')
  const [agentState, setAgentState] = useState<AgentState>(defaultAgentState)

  const productSummary = useMemo(() => {
    const realProductCount = products.filter(
      (product) => !product.id.startsWith('starter-'),
    ).length

    if (realProductCount === 0) {
      return 'Starter preview'
    }

    return `${realProductCount} live Kapruka picks`
  }, [products])

  async function sendMessage(messageText: string) {
    const trimmed = messageText.trim()
    if (!trimmed || isLoading) return

    const userMessage: Message = {
      id: Date.now(),
      role: 'user',
      text: trimmed,
    }

    setMessages((current) => [...current, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: trimmed }),
      })

      if (!response.ok) {
        throw new Error('Backend request failed')
      }

      const data = (await response.json()) as ChatResponse

      setAgentState({
        assistantName: data.assistant_name || 'Kavi',
        intentLabel: data.intent_label || 'Smart shopping',
        tone: data.tone || 'close friend',
        friendNote: data.friend_note || defaultAgentState.friendNote,
        nextActions: data.next_actions?.length
          ? data.next_actions
          : defaultAgentState.nextActions,
        resources: data.resources || [],
        safetyLevel: data.safety_level || null,
        suppressProducts: Boolean(data.suppress_products),
      })

      if (data.suppress_products) {
        setProducts([])
        setSearchContext('Shopping paused for care mode')
      } else if (data.products?.length) {
        setProducts(data.products)
        setSearchContext(
          data.search_query
            ? `Live Kapruka results for "${data.search_query}"`
            : 'Live Kapruka results',
        )
      }

      setMessages((current) => [
        ...current,
        {
          id: Date.now() + 1,
          role: 'assistant',
          text: data.reply,
        },
      ])
    } catch {
      setMessages((current) => [
        ...current,
        {
          id: Date.now() + 1,
          role: 'assistant',
          text:
            'I could not reach the shopping backend. Restart FastAPI on port 8000 and I will continue from here.',
        },
      ])
    } finally {
      setIsLoading(false)
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    void sendMessage(input)
  }

  return (
    <main className="app-shell">
      <section className="workspace" aria-label="Kavi shopping workspace">
        <aside className="sidebar" aria-label="Agent profile and context">
          <div className="brand-block">
            <span className="brand-mark">KV</span>
            <div>
              <p className="eyebrow">Kapruka AI companion</p>
              <h1>{agentState.assistantName}</h1>
            </div>
          </div>

          <div className="status-panel">
            <div>
              <span className="status-dot"></span>
              <strong>{agentState.intentLabel}</strong>
            </div>
            <p>{agentState.friendNote}</p>
          </div>

          <div className="context-grid">
            <div>
              <span>Tone</span>
              <strong>{agentState.tone}</strong>
            </div>
            <div>
              <span>Catalog</span>
              <strong>Kapruka MCP live</strong>
            </div>
            <div>
              <span>Modes</span>
              <strong>Self, gift, care</strong>
            </div>
            <div>
              <span>Language</span>
              <strong>EN / Sinhala / Tanglish</strong>
            </div>
          </div>
        </aside>

        <section className="conversation-panel" aria-label="Shopping chat">
          <div className="chat-header">
            <div>
              <p className="eyebrow">Ask like you text a friend</p>
              <h2>What are we solving today?</h2>
            </div>
            <span
              className={`header-pill ${
                agentState.safetyLevel ? 'care-pill' : ''
              }`}
            >
              {agentState.safetyLevel ? 'Care mode active' : productSummary}
            </span>
          </div>

          <div className="message-list">
            {messages.map((message) => (
              <article className={`message ${message.role}`} key={message.id}>
                <span>
                  {message.role === 'assistant'
                    ? agentState.assistantName
                    : 'You'}
                </span>
                <p>{message.text}</p>
              </article>
            ))}
            {isLoading && (
              <article className="message assistant">
                <span>{agentState.assistantName}</span>
                <p>Reading the situation, checking Kapruka, and thinking through the best move...</p>
              </article>
            )}
          </div>

          <div className="quick-prompts" aria-label="Example prompts">
            {quickPrompts.map((prompt) => (
              <button
                type="button"
                key={prompt}
                onClick={() => void sendMessage(prompt)}
              >
                {prompt}
              </button>
            ))}
          </div>

          <form className="composer" onSubmit={handleSubmit}>
            <input
              aria-label="Message"
              placeholder="Example: I need to fix a fight with my girlfriend and send flowers today in Colombo"
              value={input}
              onChange={(event) => setInput(event.target.value)}
            />
            <button type="submit" disabled={isLoading}>
              Send
            </button>
          </form>
        </section>

        <aside className="shop-panel" aria-label="Recommendations and plan">
          {agentState.suppressProducts ? (
            <div className="care-card">
              <div className="section-title">
                <p className="eyebrow">Care resources</p>
                <h2>Get support now</h2>
                <span>Shopping is paused for this conversation.</span>
              </div>
              <div className="resource-list">
                {agentState.resources.map((resource) => (
                  <article className="resource-card" key={resource.name}>
                    <strong>{resource.contact}</strong>
                    <h3>{resource.name}</h3>
                    <p>{resource.detail}</p>
                  </article>
                ))}
              </div>
            </div>
          ) : (
            <div className="panel-section">
              <div className="section-title">
                <p className="eyebrow">Kavi recommends</p>
                <h2>Live product picks</h2>
                <span>{searchContext}</span>
              </div>

              <div className="product-list">
                {products.map((product) => (
                  <article className="product-card" key={product.id}>
                    {product.image ? (
                      <img src={product.image} alt={product.name} />
                    ) : (
                      <div className="image-fallback">KV</div>
                    )}
                    <div>
                      <span>{product.category}</span>
                      <h3>{product.name}</h3>
                      <p>{product.note}</p>
                      <div className="product-footer">
                        <strong>{product.price}</strong>
                        {product.in_stock !== undefined && (
                          <small>
                            {product.in_stock ? 'In stock' : 'Check stock'}
                          </small>
                        )}
                      </div>
                      {product.url && (
                        <a href={product.url} target="_blank" rel="noreferrer">
                          View on Kapruka
                        </a>
                      )}
                    </div>
                  </article>
                ))}
              </div>
            </div>
          )}

          <div className="plan-card">
            <div className="section-title">
              <p className="eyebrow">Next best moves</p>
              <h2>{agentState.intentLabel}</h2>
            </div>
            <ol>
              {agentState.nextActions.map((action) => (
                <li key={action}>{action}</li>
              ))}
            </ol>
            <button type="button" className="checkout-button">
              {agentState.suppressProducts
                ? 'Keep Kavi with me'
                : 'Build checkout plan'}
            </button>
          </div>
        </aside>
      </section>
    </main>
  )
}

export default App
