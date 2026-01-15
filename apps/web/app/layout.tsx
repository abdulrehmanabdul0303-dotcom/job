import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { Toaster } from '@/components/ui/toaster'
import { Providers } from './providers'
import { cn } from '@/lib/utils/cn'
import '@/styles/globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: {
    default: 'JobPilot AI - Your 24/7 Job Search Assistant',
    template: '%s | JobPilot AI'
  },
  description: 'AI-powered job search platform with resume optimization, job matching, and interview prep. Get your resume score, find perfect job matches, and ace interviews with AI assistance.',
  keywords: ['job search', 'AI resume', 'job matching', 'career', 'resume score', 'interview prep', 'ATS optimization'],
  authors: [{ name: 'JobPilot AI' }],
  creator: 'JobPilot AI',
  publisher: 'JobPilot AI',
  metadataBase: new URL(process.env.NEXT_PUBLIC_BASE_URL || 'http://localhost:3000'),
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: '/',
    siteName: 'JobPilot AI',
    title: 'JobPilot AI - Your 24/7 Job Search Assistant',
    description: 'AI-powered job search platform with resume optimization, job matching, and interview prep',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: 'JobPilot AI',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'JobPilot AI - Your 24/7 Job Search Assistant',
    description: 'AI-powered job search platform with resume optimization, job matching, and interview prep',
    images: ['/og-image.png'],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={cn(
          "min-h-screen bg-background text-foreground antialiased",
          inter.className,
        )}
      >
        <Providers>
          {children}
          <Toaster />
        </Providers>
      </body>
    </html>
  )
}
