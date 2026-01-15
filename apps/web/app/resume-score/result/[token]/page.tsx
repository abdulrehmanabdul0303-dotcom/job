'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { apiUrl } from '@/lib/api';

interface PublicScorecard {
  ats_score: number;
  breakdown: {
    contact_score: number;
    sections_score: number;
    keywords_score: number;
    formatting_score: number;
    impact_score: number;
  };
  missing_keywords: string[];
  formatting_issues: string[];
  suggestions: string[];
  strengths: string[];
  calculated_at: string;
}

export default function PublicScorecardPage() {
  const params = useParams();
  const router = useRouter();
  const token = params.token as string;
  const [scorecard, setScorecard] = useState<PublicScorecard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchScorecard = async () => {
      try {
        const response = await fetch(apiUrl(`/api/v1/resume/public/${token}`));

        if (!response.ok) {
          throw new Error('Scorecard not found or link has expired');
        }

        const data = await response.json();
        setScorecard(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load scorecard');
      } finally {
        setLoading(false);
      }
    };

    fetchScorecard();
  }, [token]);

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreLabel = (score: number) => {
    if (score >= 80) return 'Excellent';
    if (score >= 60) return 'Good';
    if (score >= 40) return 'Fair';
    return 'Needs Work';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading scorecard...</p>
        </div>
      </div>
    );
  }

  if (error || !scorecard) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-xl p-8 max-w-md text-center">
          <svg className="mx-auto h-16 w-16 text-red-500 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Scorecard Not Found</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <button
            onClick={() => router.push('/')}
            className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700"
          >
            Go to Homepage
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Resume ATS Score</h1>
          <p className="text-gray-600">Shared scorecard • Privacy-protected</p>
        </div>

        {/* CTA Banner */}
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-lg shadow-lg p-6 mb-8 text-center">
          <h2 className="text-2xl font-bold text-white mb-2">Want Your Own ATS Score?</h2>
          <p className="text-blue-100 mb-4">Upload your resume and get instant feedback - 100% FREE</p>
          <button
            onClick={() => router.push('/register')}
            className="bg-white text-blue-600 px-8 py-3 rounded-lg font-semibold hover:bg-blue-50 transition-colors"
          >
            Create Free Account
          </button>
        </div>

        <div className="space-y-6">
          {/* Overall Score */}
          <div className="bg-white rounded-lg shadow-lg p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Overall ATS Score</h2>
            <div className="flex items-center space-x-8">
              <div className={`text-7xl font-bold ${getScoreColor(scorecard.ats_score)}`}>
                {scorecard.ats_score}
              </div>
              <div>
                <p className="text-3xl font-semibold text-gray-700">/ 100</p>
                <p className={`text-xl font-medium ${getScoreColor(scorecard.ats_score)}`}>
                  {getScoreLabel(scorecard.ats_score)}
                </p>
              </div>
            </div>
          </div>

          {/* Score Breakdown */}
          <div className="bg-white rounded-lg shadow-lg p-8">
            <h3 className="text-xl font-bold text-gray-900 mb-6">Score Breakdown</h3>
            <div className="space-y-4">
              {[
                { label: 'Contact Information', score: scorecard.breakdown.contact_score, max: 20 },
                { label: 'Resume Sections', score: scorecard.breakdown.sections_score, max: 20 },
                { label: 'Keywords & Skills', score: scorecard.breakdown.keywords_score, max: 30 },
                { label: 'ATS Formatting', score: scorecard.breakdown.formatting_score, max: 15 },
                { label: 'Impact Statements', score: scorecard.breakdown.impact_score, max: 15 },
              ].map((item) => (
                <div key={item.label}>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="font-medium text-gray-700">{item.label}</span>
                    <span className="font-bold text-gray-900">{item.score}/{item.max}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div
                      className={`h-3 rounded-full ${
                        item.score / item.max >= 0.8 ? 'bg-green-500' :
                        item.score / item.max >= 0.6 ? 'bg-yellow-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${(item.score / item.max) * 100}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Strengths */}
          {scorecard.strengths.length > 0 && (
            <div className="bg-white rounded-lg shadow-lg p-8">
              <h3 className="text-xl font-bold text-gray-900 mb-4">✨ Strengths</h3>
              <ul className="space-y-3">
                {scorecard.strengths.map((strength, idx) => (
                  <li key={idx} className="flex items-start">
                    <span className="text-green-500 text-xl mr-3">✓</span>
                    <span className="text-gray-700 text-lg">{strength}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Suggestions */}
          {scorecard.suggestions.length > 0 && (
            <div className="bg-white rounded-lg shadow-lg p-8">
              <h3 className="text-xl font-bold text-gray-900 mb-4">💡 Improvement Suggestions</h3>
              <ul className="space-y-3">
                {scorecard.suggestions.map((suggestion, idx) => (
                  <li key={idx} className="flex items-start">
                    <span className="text-blue-500 text-xl mr-3">→</span>
                    <span className="text-gray-700 text-lg">{suggestion}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Missing Keywords */}
          {scorecard.missing_keywords.length > 0 && (
            <div className="bg-white rounded-lg shadow-lg p-8">
              <h3 className="text-xl font-bold text-gray-900 mb-4">🔑 Consider Adding These Keywords</h3>
              <div className="flex flex-wrap gap-3">
                {scorecard.missing_keywords.slice(0, 15).map((keyword, idx) => (
                  <span
                    key={idx}
                    className="px-4 py-2 bg-yellow-100 text-yellow-800 rounded-full font-medium"
                  >
                    {keyword}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Formatting Issues */}
          {scorecard.formatting_issues.length > 0 && (
            <div className="bg-white rounded-lg shadow-lg p-8">
              <h3 className="text-xl font-bold text-gray-900 mb-4">⚠️ Formatting Issues</h3>
              <ul className="space-y-3">
                {scorecard.formatting_issues.map((issue, idx) => (
                  <li key={idx} className="flex items-start">
                    <span className="text-orange-500 text-xl mr-3">!</span>
                    <span className="text-gray-700 text-lg">{issue}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Bottom CTA */}
          <div className="bg-gradient-to-r from-purple-600 to-pink-600 rounded-lg shadow-lg p-8 text-center">
            <h2 className="text-3xl font-bold text-white mb-3">Ready to Improve Your Resume?</h2>
            <p className="text-purple-100 text-lg mb-6">
              Join JobPilot AI and get personalized job matches + auto-apply assistance
            </p>
            <div className="flex justify-center space-x-4">
              <button
                onClick={() => router.push('/register')}
                className="bg-white text-purple-600 px-8 py-3 rounded-lg font-semibold hover:bg-purple-50 transition-colors"
              >
                Sign Up Free
              </button>
              <button
                onClick={() => router.push('/resume-score')}
                className="bg-purple-700 text-white px-8 py-3 rounded-lg font-semibold hover:bg-purple-800 transition-colors"
              >
                Score My Resume
              </button>
            </div>
          </div>
        </div>

        {/* Footer Note */}
        <div className="text-center mt-8 text-sm text-gray-600">
          <p>🔒 This scorecard contains no personal information</p>
          <p className="mt-1">Analyzed on {new Date(scorecard.calculated_at).toLocaleDateString()}</p>
        </div>
      </div>
    </div>
  );
}
