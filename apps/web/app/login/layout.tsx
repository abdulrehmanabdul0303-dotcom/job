import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Sign In | JobPilot AI',
  description: 'Sign in to your JobPilot AI account to access your personalized job matches, resume scores, and application tracking. Your 24/7 AI job agent awaits.',
  robots: {
    index: false, // Don't index login page
    follow: true,
  },
  alternates: {
    canonical: '/login',
  },
}

export default function LoginLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return children
}
