'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { 
  Search, 
  MapPin, 
  Building, 
  Clock,
  DollarSign,
  Filter,
  Briefcase,
  ExternalLink
} from 'lucide-react'
import { jobsApi, JobSearchParams } from '@/lib/api/jobs'
import { formatSalary, formatDate } from '@/lib/utils/format'

export default function JobsPage() {
  const [searchParams, setSearchParams] = useState<JobSearchParams>({
    search: '',
    location: '',
    remote: undefined,
    job_type: '',
    page: 1,
    limit: 20,
  })

  // Fetch jobs
  const { data: jobsData, isLoading } = useQuery({
    queryKey: ['jobs', searchParams],
    queryFn: () => jobsApi.search(searchParams),
  })

  const handleSearch = (field: keyof JobSearchParams, value: any) => {
    setSearchParams(prev => ({
      ...prev,
      [field]: value,
      page: 1, // Reset to first page when searching
    }))
  }

  const clearFilters = () => {
    setSearchParams({
      search: '',
      location: '',
      remote: undefined,
      job_type: '',
      page: 1,
      limit: 20,
    })
  }

  const jobTypeOptions = [
    { value: '', label: 'All Types' },
    { value: 'full-time', label: 'Full-time' },
    { value: 'part-time', label: 'Part-time' },
    { value: 'contract', label: 'Contract' },
    { value: 'internship', label: 'Internship' },
  ]

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Job Search</h1>
            <p className="text-muted-foreground mt-2">
              Discover opportunities that match your skills and preferences
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <Button variant="outline" onClick={clearFilters}>
              Clear Filters
            </Button>
            <Button>
              <Filter className="mr-2 h-4 w-4" />
              Advanced Filters
            </Button>
          </div>
        </div>
      </motion.div>

      {/* Search and Filters */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.1 }}
      >
        <Card>
          <CardContent className="pt-6">
            <div className="grid gap-4 md:grid-cols-4">
              {/* Search */}
              <div className="md:col-span-2">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search jobs, companies, or keywords..."
                    value={searchParams.search}
                    onChange={(e) => handleSearch('search', e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>

              {/* Location */}
              <div>
                <div className="relative">
                  <MapPin className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Location"
                    value={searchParams.location}
                    onChange={(e) => handleSearch('location', e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>

              {/* Job Type */}
              <div>
                <select
                  value={searchParams.job_type}
                  onChange={(e) => handleSearch('job_type', e.target.value)}
                  className="w-full h-10 px-3 rounded-md border border-input bg-background text-sm"
                >
                  {jobTypeOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Remote Toggle */}
            <div className="flex items-center space-x-4 mt-4">
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={searchParams.remote === true}
                  onChange={(e) => handleSearch('remote', e.target.checked ? true : undefined)}
                  className="rounded border-input"
                />
                <span className="text-sm">Remote jobs only</span>
              </label>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Results */}
      <div className="space-y-4">
        {/* Results Header */}
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            {jobsData ? `${jobsData.total} jobs found` : 'Loading...'}
          </p>
          <div className="flex items-center space-x-2">
            <span className="text-sm text-muted-foreground">Sort by:</span>
            <select className="text-sm border-0 bg-transparent">
              <option>Relevance</option>
              <option>Date Posted</option>
              <option>Salary</option>
            </select>
          </div>
        </div>

        {/* Job Cards */}
        {isLoading ? (
          <div className="space-y-4">
            {[...Array(5)].map((_, i) => (
              <Card key={i}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="space-y-2 flex-1">
                      <Skeleton className="h-6 w-3/4" />
                      <Skeleton className="h-4 w-1/2" />
                      <div className="flex space-x-2">
                        <Skeleton className="h-6 w-16" />
                        <Skeleton className="h-6 w-20" />
                      </div>
                    </div>
                    <Skeleton className="h-10 w-24" />
                  </div>
                </CardHeader>
                <CardContent>
                  <Skeleton className="h-16 w-full" />
                </CardContent>
              </Card>
            ))}
          </div>
        ) : jobsData && jobsData.jobs.length > 0 ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="space-y-4"
          >
            {jobsData.jobs.map((job, index) => (
              <motion.div
                key={job.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.05 }}
              >
                <Card className="hover:shadow-lg transition-shadow">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          <CardTitle className="text-xl hover:text-primary cursor-pointer">
                            <Link href={`/app/jobs/${job.id}`}>
                              {job.title}
                            </Link>
                          </CardTitle>
                          {job.remote && (
                            <Badge variant="secondary">Remote</Badge>
                          )}
                        </div>
                        
                        <div className="flex items-center space-x-4 text-sm text-muted-foreground mb-3">
                          <div className="flex items-center space-x-1">
                            <Building className="h-4 w-4" />
                            <span>{job.company}</span>
                          </div>
                          {job.location && (
                            <div className="flex items-center space-x-1">
                              <MapPin className="h-4 w-4" />
                              <span>{job.location}</span>
                            </div>
                          )}
                          <div className="flex items-center space-x-1">
                            <Clock className="h-4 w-4" />
                            <span>{formatDate(job.posted_at)}</span>
                          </div>
                        </div>

                        <div className="flex items-center space-x-2 mb-3">
                          <Badge variant="outline">
                            {job.job_type.replace('-', ' ')}
                          </Badge>
                          <Badge variant="outline">
                            {job.seniority_level}
                          </Badge>
                          {job.salary_min && job.salary_max && (
                            <Badge variant="outline" className="flex items-center space-x-1">
                              <DollarSign className="h-3 w-3" />
                              <span>
                                {formatSalary(job.salary_min)} - {formatSalary(job.salary_max)}
                              </span>
                            </Badge>
                          )}
                        </div>

                        <CardDescription className="line-clamp-2">
                          {job.description}
                        </CardDescription>
                      </div>

                      <div className="flex flex-col space-y-2 ml-4">
                        <Button asChild>
                          <Link href={`/app/jobs/${job.id}`}>
                            View Details
                          </Link>
                        </Button>
                        {job.external_url && (
                          <Button variant="outline" size="sm" asChild>
                            <a href={job.external_url} target="_blank" rel="noopener noreferrer">
                              <ExternalLink className="mr-2 h-4 w-4" />
                              Apply
                            </a>
                          </Button>
                        )}
                      </div>
                    </div>
                  </CardHeader>
                  
                  {job.skills && job.skills.length > 0 && (
                    <CardContent>
                      <div className="flex flex-wrap gap-2">
                        {job.skills.slice(0, 6).map((skill) => (
                          <Badge key={skill} variant="secondary" className="text-xs">
                            {skill}
                          </Badge>
                        ))}
                        {job.skills.length > 6 && (
                          <Badge variant="secondary" className="text-xs">
                            +{job.skills.length - 6} more
                          </Badge>
                        )}
                      </div>
                    </CardContent>
                  )}
                </Card>
              </motion.div>
            ))}
          </motion.div>
        ) : (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <Card>
              <CardContent className="text-center py-12">
                <Briefcase className="h-16 w-16 text-muted-foreground mx-auto mb-6" />
                <h3 className="text-xl font-semibold mb-2">No Jobs Found</h3>
                <p className="text-muted-foreground mb-6 max-w-md mx-auto">
                  We couldn&apos;t find any jobs matching your criteria. Try adjusting your search filters.
                </p>
                <Button onClick={clearFilters}>
                  Clear All Filters
                </Button>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Pagination */}
        {jobsData && jobsData.total > jobsData.limit && (
          <div className="flex items-center justify-center space-x-2 pt-6">
            <Button
              variant="outline"
              disabled={!jobsData.has_prev}
              onClick={() => handleSearch('page', (searchParams.page || 1) - 1)}
            >
              Previous
            </Button>
            <span className="text-sm text-muted-foreground">
              Page {searchParams.page} of {Math.ceil(jobsData.total / jobsData.limit)}
            </span>
            <Button
              variant="outline"
              disabled={!jobsData.has_next}
              onClick={() => handleSearch('page', (searchParams.page || 1) + 1)}
            >
              Next
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}