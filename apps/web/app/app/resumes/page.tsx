'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { 
  FileText, 
  Upload, 
  Eye, 
  Share, 
  Trash2,
  Plus,
  Download,
  RefreshCw
} from 'lucide-react'
import { resumeApi, Resume, ResumeScorecard } from '@/lib/api/resume'
import { formatDate, formatFileSize, formatScore } from '@/lib/utils/format'
import { ResumeWithScore } from '@/lib/types'
import { toast } from '@/hooks/use-toast'

export default function ResumesPage() {
  const [uploadProgress, setUploadProgress] = useState(0)
  const queryClient = useQueryClient()

  // Fetch resumes with scorecards
  const { data: resumes, isLoading } = useQuery<ResumeWithScore[]>({
    queryKey: ['resumes'],
    queryFn: async () => {
      const resumeList = await resumeApi.list()
      // Fetch scorecards for each resume
      const resumesWithScores = await Promise.all(
        resumeList.map(async (resume): Promise<ResumeWithScore> => {
          try {
            const scorecard = await resumeApi.getScorecard(resume.id)
            return { ...resume, scorecard }
          } catch {
            // If scorecard doesn't exist, return resume without it
            return resume
          }
        })
      )
      return resumesWithScores
    },
  })

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: (file: File) => resumeApi.upload(file, setUploadProgress),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['resumes'] })
      setUploadProgress(0)
      toast({
        title: "Resume Uploaded",
        description: "Your resume has been uploaded and is being processed.",
        variant: "success",
      })
    },
    onError: (error: any) => {
      setUploadProgress(0)
      toast({
        title: "Upload Failed",
        description: error.message || "Failed to upload resume. Please try again.",
        variant: "destructive",
      })
    },
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: resumeApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['resumes'] })
      toast({
        title: "Resume Deleted",
        description: "Your resume has been deleted successfully.",
        variant: "success",
      })
    },
    onError: (error: any) => {
      toast({
        title: "Delete Failed",
        description: error.message || "Failed to delete resume. Please try again.",
        variant: "destructive",
      })
    },
  })

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      // Validate file type
      const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
      if (!allowedTypes.includes(file.type)) {
        toast({
          title: "Invalid File Type",
          description: "Please upload a PDF or DOCX file.",
          variant: "destructive",
        })
        return
      }

      // Validate file size (5MB)
      if (file.size > 5 * 1024 * 1024) {
        toast({
          title: "File Too Large",
          description: "Please upload a file smaller than 5MB.",
          variant: "destructive",
        })
        return
      }

      uploadMutation.mutate(file)
    }
  }

  const handleDelete = (id: string) => {
    if (confirm('Are you sure you want to delete this resume?')) {
      deleteMutation.mutate(id)
    }
  }

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
            <h1 className="text-3xl font-bold">Resumes</h1>
            <p className="text-muted-foreground mt-2">
              Upload and manage your resumes, get ATS scores and optimization suggestions
            </p>
          </div>
          <div className="flex items-center space-x-4">
            <input
              type="file"
              accept=".pdf,.docx"
              onChange={handleFileUpload}
              className="hidden"
              id="resume-upload"
            />
            <Button asChild>
              <label htmlFor="resume-upload" className="cursor-pointer">
                <Plus className="mr-2 h-4 w-4" />
                Upload Resume
              </label>
            </Button>
          </div>
        </div>
      </motion.div>

      {/* Upload Progress */}
      {uploadMutation.isPending && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-muted/50 rounded-lg p-4"
        >
          <div className="flex items-center space-x-4">
            <Upload className="h-5 w-5 text-primary" />
            <div className="flex-1">
              <p className="text-sm font-medium">Uploading resume...</p>
              <div className="w-full bg-muted rounded-full h-2 mt-2">
                <div 
                  className="bg-primary h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
            <span className="text-sm text-muted-foreground">{uploadProgress}%</span>
          </div>
        </motion.div>
      )}

      {/* Resumes Grid */}
      {isLoading ? (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {[...Array(6)].map((_, i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-6 w-3/4" />
                <Skeleton className="h-4 w-1/2" />
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-2/3" />
                  <div className="flex space-x-2">
                    <Skeleton className="h-8 w-16" />
                    <Skeleton className="h-8 w-16" />
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : resumes && resumes.length > 0 ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="grid gap-6 md:grid-cols-2 lg:grid-cols-3"
        >
          {resumes.map((resume, index) => (
            <motion.div
              key={resume.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: index * 0.1 }}
            >
              <Card className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="p-2 bg-primary/10 rounded">
                        <FileText className="h-5 w-5 text-primary" />
                      </div>
                      <div>
                        <CardTitle className="text-lg truncate">
                          {resume.filename}
                        </CardTitle>
                        <CardDescription>
                          {formatFileSize(resume.file_size)} • {formatDate(resume.uploaded_at)}
                        </CardDescription>
                      </div>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {/* ATS Score */}
                    {resume.scorecard?.ats_score ? (
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">ATS Score</span>
                        <Badge 
                          variant={resume.scorecard.ats_score >= 80 ? "success" : resume.scorecard.ats_score >= 60 ? "warning" : "destructive"}
                        >
                          {formatScore(resume.scorecard.ats_score)}/100
                        </Badge>
                      </div>
                    ) : (
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">Status</span>
                        <Badge variant="secondary">
                          {resume.is_parsed ? 'Processed' : 'Processing...'}
                        </Badge>
                      </div>
                    )}

                    {/* Actions */}
                    <div className="flex items-center space-x-2">
                      <Button size="sm" variant="outline" className="flex-1">
                        <Eye className="mr-2 h-4 w-4" />
                        View
                      </Button>
                      <Button size="sm" variant="outline">
                        <Share className="h-4 w-4" />
                      </Button>
                      <Button size="sm" variant="outline">
                        <Download className="h-4 w-4" />
                      </Button>
                      <Button 
                        size="sm" 
                        variant="outline"
                        onClick={() => handleDelete(resume.id)}
                        disabled={deleteMutation.isPending}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
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
              <FileText className="h-16 w-16 text-muted-foreground mx-auto mb-6" />
              <h3 className="text-xl font-semibold mb-2">No Resumes Yet</h3>
              <p className="text-muted-foreground mb-6 max-w-md mx-auto">
                Upload your first resume to get started with ATS scoring and job matching.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Button asChild>
                  <label htmlFor="resume-upload" className="cursor-pointer">
                    <Upload className="mr-2 h-4 w-4" />
                    Upload Your First Resume
                  </label>
                </Button>
                <Button variant="outline">
                  <FileText className="mr-2 h-4 w-4" />
                  Learn About ATS Scores
                </Button>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Tips Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.4 }}
      >
        <Card>
          <CardHeader>
            <CardTitle>Resume Tips</CardTitle>
            <CardDescription>
              Get the most out of your resume uploads
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              <div className="flex items-start space-x-3">
                <div className="p-2 bg-blue-100 rounded">
                  <FileText className="h-4 w-4 text-blue-600" />
                </div>
                <div>
                  <h4 className="font-medium">Supported Formats</h4>
                  <p className="text-sm text-muted-foreground">
                    Upload PDF or DOCX files up to 5MB
                  </p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <div className="p-2 bg-green-100 rounded">
                  <RefreshCw className="h-4 w-4 text-green-600" />
                </div>
                <div>
                  <h4 className="font-medium">ATS Optimization</h4>
                  <p className="text-sm text-muted-foreground">
                    Get instant feedback on ATS compatibility
                  </p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <div className="p-2 bg-purple-100 rounded">
                  <Share className="h-4 w-4 text-purple-600" />
                </div>
                <div>
                  <h4 className="font-medium">Share Safely</h4>
                  <p className="text-sm text-muted-foreground">
                    Create privacy-safe public scorecards
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  )
}