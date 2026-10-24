import { Component, type ErrorInfo, type ReactNode } from 'react'

interface Props {
  children: ReactNode
  label?: string
}

interface State {
  hasError: boolean
  message?: string
}

/** Prevent a single delight feature from crashing the whole app. */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, message: error.message }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('RxGuard panel error', this.props.label, error, info.componentStack)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div
          role="alert"
          className="rounded-2xl border border-[#FED7AA] bg-[#FFF7ED] px-4 py-3 text-sm text-[#B45309]"
        >
          <p className="font-semibold">
            {this.props.label || 'This panel'} could not be shown.
          </p>
          <p className="mt-1 text-xs opacity-80">
            The rest of the report is still available. {this.state.message}
          </p>
          <button
            type="button"
            className="mt-2 text-xs underline"
            onClick={() => this.setState({ hasError: false, message: undefined })}
          >
            Try again
          </button>
        </div>
      )
    }
    return this.props.children
  }
}
