import { MetadataRoute } from 'next'

/**
 * Sitemap for JobPilot AI
 * 
 * Helps search engines discover and index all pages.
 * Updates automatically on build.
 */
export default function sitemap(): MetadataRoute.Sitemap {
  const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || 'https://jobpilot.ai'
  const currentDate = new Date()

  return [
    // Public pages (high priority)
    {
      url: baseUrl,
      lastModified: currentDate,
      changeFrequency: 'daily',
      priority: 1.0,
    },
    {
      url: `${baseUrl}/resume-score`,
      lastModified: currentDate,
      changeFrequency: 'weekly',
      priority: 0.9,
    },
    {
      url: `${baseUrl}/login`,
      lastModified: currentDate,
      changeFrequency: 'monthly',
      priority: 0.7,
    },
    {
      url: `${baseUrl}/register`,
      lastModified: currentDate,
      changeFrequency: 'monthly',
      priority: 0.8,
    },
    
    // Feature pages (medium priority)
    // Note: Authenticated pages (/app/*) are excluded from sitemap
    // as they require login and shouldn't be indexed by search engines
    
    // Add more public pages here as they're created:
    // - Blog posts
    // - Help/FAQ pages
    // - Pricing page
    // - About page
    // - Contact page
    // - Public job listings (if any)
  ]
}
