import { useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import './App.css'

type Message = {
  id: number
  role: 'assistant' | 'user'
  text: string
}

type Product = {
  id: number
  name: string
  category: string
  price: string
  image: string
  note: string
}

const initialMessages: Message[] = [
  {
    id: 1,
    role: 'assistant',
    text:
      'Ayubowan Lahiru. Tell me what you need, your city, budget, and when you want it delivered. I can help with groceries, gifts, electronics, flowers, cakes, fashion, and daily essentials.',
  },
]

const featuredProducts: Product[] = [
  {
    id: 1,
    name: 'Fresh flower apology bundle',
    category: 'Gift mode',
    price: 'From Rs. 6,500',
    image:
      'https://images.unsplash.com/photo-1518709779341-56cf4535e94b?auto=format&fit=crop&w=600&q=80',
    note: 'Good when the message matters more than the item.',
  },
  {
    id: 2,
    name: 'Weekly grocery top-up',
    category: 'Everyday shopping',
    price: 'From Rs. 9,000',
    image:
      'https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&w=600&q=80',
    note: 'Built for customers buying for themselves.',
  },
  {
    id: 3,
    name: 'Smart home essentials',
    category: 'Electronics',
    price: 'From Rs. 12,500',
    image:
      'https://images.unsplash.com/photo-1558002038-1055907df827?auto=format&fit=crop&w=600&q=80',
    note: 'Useful products, not only gift recommendations.',
  },
]

const quickPrompts = [
  'I need groceries delivered to Colombo tomorrow',
  'Find a birthday gift under Rs. 10,000',
  'Mage amma ta gift ekak one',
  'I broke up and need flowers today',
]

function App() {
  const [messages, setMessages] = useState<Message[]>(initialMessages)
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const cartTotal = useMemo(() => 'Rs. 16,400', [])

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

      const data = await response.json()
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
            'I could not reach the shopping backend. Start the FastAPI server on port 8000 and try again.',
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
      <section className="workspace" aria-label="Kapruka Companion workspace">
        <aside className="sidebar" aria-label="Shopping context">
          <div className="brand-block">
            <span className="brand-mark">KC</span>
            <div>
              <p className="eyebrow">Kapruka Companion</p>
              <h1>AI shopping concierge</h1>
            </div>
          </div>

          <div className="status-panel">
            <div>
              <span className="status-dot"></span>
              <strong>Demo mode</strong>
            </div>
            <p>Frontend is connected to your Python FastAPI backend.</p>
          </div>

          <div className="context-grid">
            <div>
              <span>City</span>
              <strong>Colombo</strong>
            </div>
            <div>
              <span>Delivery</span>
              <strong>Tomorrow</strong>
            </div>
            <div>
              <span>Mode</span>
              <strong>Self + Gift</strong>
            </div>
            <div>
              <span>Language</span>
              <strong>EN / SI / Tanglish</strong>
            </div>
          </div>
        </aside>

        <section className="conversation-panel" aria-label="Shopping chat">
          <div className="chat-header">
            <div>
              <p className="eyebrow">Live assistant</p>
              <h2>Tell me what you need to buy</h2>
            </div>
            <span className="header-pill">MCP-ready</span>
          </div>

          <div className="message-list">
            {messages.map((message) => (
              <article className={`message ${message.role}`} key={message.id}>
                <span>{message.role === 'assistant' ? 'AI' : 'You'}</span>
                <p>{message.text}</p>
              </article>
            ))}
            {isLoading && (
              <article className="message assistant">
                <span>AI</span>
                <p>Checking the best path for you...</p>
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
              placeholder="Example: Find groceries for Rs. 8,000 delivered to Kandy this Friday"
              value={input}
              onChange={(event) => setInput(event.target.value)}
            />
            <button type="submit" disabled={isLoading}>
              Send
            </button>
          </form>
        </section>

        <aside className="shop-panel" aria-label="Products and cart">
          <div className="panel-section">
            <div className="section-title">
              <p className="eyebrow">Recommended</p>
              <h2>Visual picks</h2>
            </div>

            <div className="product-list">
              {featuredProducts.map((product) => (
                <article className="product-card" key={product.id}>
                  <img src={product.image} alt={product.name} />
                  <div>
                    <span>{product.category}</span>
                    <h3>{product.name}</h3>
                    <p>{product.note}</p>
                    <strong>{product.price}</strong>
                  </div>
                </article>
              ))}
            </div>
          </div>

          <div className="cart-card">
            <div className="section-title">
              <p className="eyebrow">Draft cart</p>
              <h2>3 items</h2>
            </div>
            <ul>
              <li>
                <span>Flowers</span>
                <strong>Rs. 6,500</strong>
              </li>
              <li>
                <span>Note card</span>
                <strong>Rs. 900</strong>
              </li>
              <li>
                <span>Grocery bundle</span>
                <strong>Rs. 9,000</strong>
              </li>
            </ul>
            <div className="cart-total">
              <span>Total</span>
              <strong>{cartTotal}</strong>
            </div>
            <button type="button" className="checkout-button">
              Prepare checkout
            </button>
          </div>
        </aside>
      </section>
    </main>
  )
}

export default App
