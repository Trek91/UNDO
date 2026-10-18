import { Component, StrictMode } from 'react'
import type { ErrorInfo, ReactNode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import './styles.css'

class ErrorBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false }
  static getDerivedStateFromError() { return { failed: true } }
  componentDidCatch(error: Error, info: ErrorInfo) { console.error('UNDO rendering failure', error, info.componentStack) }
  render() {
    if (this.state.failed) return <main className="recovery"><h1>The workspace couldn’t render.</h1><p>Your saved financial state is preserved. Reload to reconnect.</p><button className="primary" onClick={() => location.reload()}>Reload workspace</button></main>
    return this.props.children
  }
}
createRoot(document.getElementById('root')!).render(<StrictMode><ErrorBoundary><App/></ErrorBoundary></StrictMode>)
