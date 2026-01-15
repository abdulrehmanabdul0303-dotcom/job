import { MetadataRoute } from 'next'

/**
 * Robots.txt for JobPilot AI
 * 
 * Controls how search engines crawl the site.
 * - Allow public pages
 * - Disallow authenticated pages
 * - Disallow API routes
 */
export default function robots(): MetadataRoute.Robots {
  const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || 'https://jobpilot.ai'

  return {
    rules: [
      {
        userAgent: '*',
        allow: '/',
        disallow: [
          '/app/',           // Authenticated pages
          '/api/',           // API routes
          '/_next/',         // Next.js internals
          '/admin/',         // Admin pages (if any)
        ],
      },
      // Allow specific bots to crawl more aggressively
      {
        userAgent: 'Googlebot',
        allow: '/',
        disallow: ['/app/', '/api/', '/_next/', '/admin/'],
        crawlDelay: 0,
      },
      // Block bad bots
      {
        userAgent: [
          'AhrefsBot',
          'SemrushBot',
          'DotBot',
          'MJ12bot',
        ],
        disallow: '/',
      },
    ],
    sitemap: `${baseUrl}/sitemap.xml`,
  }
}
