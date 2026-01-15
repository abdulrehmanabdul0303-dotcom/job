'use client'

/**
 * App Routes Error Boundary
 * 
 * Catches errors in authenticated app routes.
 * Provides user-friendly error UI with recovery options.
 */

import { useEffect } from 'react'
import { Button } from '@/components/ui/button'

export default function AppError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    // Log error to error reporting service
    console.error('App error:', error)
  }, [error])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
      <div className="max-w-lg w-full bg-white rounded-lg shadow-lg p-8">
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-100 mb-4">
            <svg
              className="h-8 w-8 text-red-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            Oops! Something went wrong
          </h2>
          
          <p className="text-gray-600 mb-4">
            We encountered an error while loading this page. This has been logged and we&apos;ll look into it.
          </p>

          {process.env.NODE_ENV === 'development' && (
            <details className="text-left mt-4 p-4 bg-gray-50 rounded text-sm">
              <summary className="cursor-pointer font-medium text-gray-700 mb-2">
                Error Details (Development Only)
              </summary>
              <pre className="text-xs text-red-600 overflow-auto">
                {error.message}
              </pre>
              {error.stack && (
                <pre className="text-xs text-gray-600 overflow-auto mt-2">
                  {error.stack}
                </pre>
              )}
            </details>
          )}

          {error.digest && (
            <p className="text-xs text-gray-500 mt-4">
              Error ID: {error.digest}
            </p>
          )}
        </div>

        <div className="flex flex-col sm:flex-row gap-3">
          <Button
            onClick={reset}
            className="flex-1 bg-blue-600 hover:bg-blue-700"
          >
            Try Again
          </Button>
          
          <Button
            onClick={() => window.location.href = '/app/dashboard'}
            variant="outline"
            className="flex-1"
          >
            Go to Dashboard
          </Button>
        </div>

        <div className="mt-6 pt-6 border-t text-center">
          <p className="text-sm text-gray-600 mb-2">
            Need help?
          </p>
          <a
            href="mailto:support@jobpilot.ai"
            className="text-sm text-blue-600 hover:text-blue-700"
          >
            Contact Support
          </a>
        </div>
      </div>
    </div>
  )
}
