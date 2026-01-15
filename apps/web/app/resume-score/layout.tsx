import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Free ATS Resume Score | JobPilot AI',
  description: 'Upload your resume and get instant ATS score with detailed feedback. 100% free, no signup required. Optimize your resume for applicant tracking systems with AI-powered suggestions.',
  keywords: ['ATS score', 'resume checker', 'free resume score', 'ATS optimization', 'resume feedback', 'applicant tracking system', 'resume analyzer'],
  openGraph: {
    title: 'Free ATS Resume Score | JobPilot AI',
    description: 'Get instant ATS score for your resume with AI-powered feedback. Upload now - 100% free!',
    type: 'website',
    url: '/resume-score',
    images: [
      {
        url: '/og-resume-score.png',
        width: 1200,
        height: 630,
        alt: 'Free ATS Resume Score Tool',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Free ATS Resume Score | JobPilot AI',
    description: 'Get instant ATS score for your resume with AI-powered feedback',
    images: ['/og-resume-score.png'],
  },
  alternates: {
    canonical: '/resume-score',
  },
}

export default function ResumeScoreLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return children
}
