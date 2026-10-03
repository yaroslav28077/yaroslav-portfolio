import { Component } from 'react'
import type { ReactNode } from 'react'

interface SceneBoundaryProps {
  onError: (error: Error) => void
  children: ReactNode
}

/** Ловить помилки створення WebGL і рендера 3D-сцени; CSS-віяло лишається робочим. */
export class SceneBoundary extends Component<SceneBoundaryProps, { failed: boolean }> {
  override state = { failed: false }

  static getDerivedStateFromError() {
    return { failed: true }
  }

  override componentDidCatch(error: Error) {
    this.props.onError(error)
  }

  override render() {
    return this.state.failed ? null : this.props.children
  }
}
