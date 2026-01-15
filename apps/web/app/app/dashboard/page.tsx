'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { toast } from '@/hooks/use-toast'
import { getCurrentUser, logout } from '@/lib/auth'
import type { User } from '@/lib/auth'

export default function DashboardPage() {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const router = useRouter()

  useEffect(() => {
    getCurrentUser()
      .then(setUser)
      .catch((err) => {
        setError(err.message)
        if (err.message.includes('401') || err.message.includes('Unauthorized')) {
          router.push('/login')
        }
      })
      .finally(() => setIsLoading(false))
  }, [router])

  const handleLogout = async () => {
    try {
      await logout()
      toast({
        title: "Success",
        description: "You have been logged out successfully.",
        variant: "success"
      })
      router.push('/')
    } catch (error) {
      toast({
        title: "Error",
        description: "Logout failed. Please try again.",
        variant: "destructive"
      })
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  if (error && !user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle className="text-red-600">Error</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-red-600 mb-4">{error}</p>
            <Button onClick={() => router.push('/login')} className="w-full">
              Go to Login
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <Button onClick={handleLogout} variant="outline">
            Logout
          </Button>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Welcome Back!</CardTitle>
              <CardDescription>
                Your JobPilot AI dashboard
              </CardDescription>
            </CardHeader>
            <CardContent>
              {user && (
                <div className="space-y-2">
                  <p><strong>Name:</strong> {user.full_name}</p>
                  <p><strong>Email:</strong> {user.email}</p>
                  <p><strong>Account Status:</strong> {user.is_active ? 'Active' : 'Inactive'}</p>
                  <p><strong>Member Since:</strong> {new Date(user.created_at).toLocaleDateString()}</p>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
              <CardDescription>
                Get started with JobPilot AI
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button className="w-full" onClick={() => router.push('/app/resumes')}>
                Upload Resume
              </Button>
              <Button className="w-full" variant="outline" onClick={() => router.push('/app/jobs')}>
                Browse Jobs
              </Button>
              <Button className="w-full" variant="outline" onClick={() => router.push('/app/preferences')}>
                Set Preferences
              </Button>
            </CardContent>
          </Card>
        </div>

        {user && (
          <Card className="mt-6">
            <CardHeader>
              <CardTitle>Debug Info</CardTitle>
              <CardDescription>
                Authentication details (for testing)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <pre className="bg-gray-100 p-4 rounded text-sm overflow-auto">
                {JSON.stringify(user, null, 2)}
              </pre>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}