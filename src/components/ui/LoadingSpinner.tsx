
import { FC } from 'react'
import { Spinner } from 'react-bootstrap'

interface LoadingSpinnerProps {
  size?: 'sm' | 'lg'
  variant?: 'primary' | 'secondary' | 'light' | 'dark'
  text?: string
  fullScreen?: boolean
}

export const LoadingSpinner: FC<LoadingSpinnerProps> = ({
  size = 'sm',
  variant = 'primary',
  text = 'Loading...',
  fullScreen = false,
}) => {
  const spinner = (
    <div className={`d-flex align-items-center ${fullScreen ? 'justify-content-center' : ''}`}>
      <Spinner animation="border" size={size} variant={variant} className="me-2" />
      {text && <span className="text-muted">{text}</span>}
    </div>
  )

  if (fullScreen) {
    return (
      <div 
        className="position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center"
        style={{ backgroundColor: 'rgba(255, 255, 255, 0.8)', zIndex: 9999 }}
      >
        {spinner}
      </div>
    )
  }

  return spinner
}
