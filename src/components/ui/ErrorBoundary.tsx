
'use client'

import { Component, ErrorInfo, ReactNode } from 'react'
import { Alert, Button, Container } from 'react-bootstrap'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error?: Error
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
  }

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error boundary caught an error:', error, errorInfo)
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: undefined })
  }

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <Container className="mt-5">
          <Alert variant="danger">
            <Alert.Heading>Something went wrong</Alert.Heading>
            <p>
              We're sorry, but something unexpected happened. Please try refreshing the page.
            </p>
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <details className="mt-3">
                <summary>Error Details (Development)</summary>
                <pre className="mt-2 p-2 bg-light rounded">
                  {this.state.error.message}
                  {this.state.error.stack}
                </pre>
              </details>
            )}
            <hr />
            <div className="d-flex gap-2">
              <Button variant="outline-danger" onClick={this.handleReset}>
                Try Again
              </Button>
              <Button variant="outline-secondary" onClick={() => window.location.reload()}>
                Refresh Page
              </Button>
            </div>
          </Alert>
        </Container>
      )
    }

    return this.props.children
  }
}
