import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Create Free Account | JobPilot AI',
  description: 'Create your free JobPilot AI account and start finding your dream job with AI-powered job matching, resume optimization, and application assistance. No credit card required.',
  keywords: ['job search', 'create account', 'free signup', 'AI job agent', 'job automation', 'career platform'],
  openGraph: {
    title: 'Create Free Account | JobPilot AI',
    description: 'Start finding your dream job with AI-powered assistance. 100% free forever.',
    type: 'website',
    url: '/register',
    images: [
      {
        url: '/og-register.png',
        width: 1200,
        height: 630,
        alt: 'Join JobPilot AI',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Create Free Account | JobPilot AI',
    description: 'Start finding your dream job with AI-powered assistance',
    images: ['/og-register.png'],
  },
  alternates: {
    canonical: '/register',
  },
}

export default function RegisterLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return children
}
