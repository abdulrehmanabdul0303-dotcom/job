'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { motion } from 'framer-motion'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { 
  Settings, 
  MapPin, 
  DollarSign, 
  Briefcase,
  Save,
  Plus,
  X
} from 'lucide-react'
import { preferencesApi, UpdatePreferencesRequest } from '@/lib/api/preferences'
import { toast } from '@/hooks/use-toast'

interface PreferencesForm {
  desired_role: string
  desired_locations: string[]
  job_types: string[]
  salary_min: number
  salary_max: number
  remote_preference: string
  skills: string[]
}

export default function PreferencesPage() {
  const [newSkill, setNewSkill] = useState('')
  const [newLocation, setNewLocation] = useState('')
  const queryClient = useQueryClient()

  // Fetch preferences
  const { data: preferences, isLoading } = useQuery({
    queryKey: ['preferences'],
    queryFn: preferencesApi.get,
  })

  // Form setup
  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isDirty },
  } = useForm<PreferencesForm>({
    defaultValues: {
      desired_role: preferences?.desired_role || '',
      desired_locations: preferences?.desired_locations || [],
      job_types: preferences?.job_types || [],
      salary_min: preferences?.salary_min || 0,
      salary_max: preferences?.salary_max || 0,
      remote_preference: preferences?.remote_preference || 'no-preference',
      skills: preferences?.skills || [],
    },
  })

  const watchedSkills = watch('skills') || []
  const watchedLocations = watch('desired_locations') || []
  const watchedJobTypes = watch('job_types') || []

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: (data: UpdatePreferencesRequest) => preferencesApi.update(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['preferences'] })
      toast({
        title: "Preferences Updated",
        description: "Your job preferences have been saved successfully.",
        variant: "success",
      })
    },
    onError: (error: any) => {
      toast({
        title: "Update Failed",
        description: error.message || "Failed to update preferences. Please try again.",
        variant: "destructive",
      })
    },
  })

  const onSubmit = (data: PreferencesForm) => {
    updateMutation.mutate(data)
  }

  const addSkill = () => {
    if (newSkill.trim() && !watchedSkills.includes(newSkill.trim())) {
      setValue('skills', [...watchedSkills, newSkill.trim()], { shouldDirty: true })
      setNewSkill('')
    }
  }

  const removeSkill = (skill: string) => {
    setValue('skills', watchedSkills.filter(s => s !== skill), { shouldDirty: true })
  }

  const addLocation = () => {
    if (newLocation.trim() && !watchedLocations.includes(newLocation.trim())) {
      setValue('desired_locations', [...watchedLocations, newLocation.trim()], { shouldDirty: true })
      setNewLocation('')
    }
  }

  const removeLocation = (location: string) => {
    setValue('desired_locations', watchedLocations.filter(l => l !== location), { shouldDirty: true })
  }

  const toggleJobType = (jobType: string) => {
    const current = watchedJobTypes
    const updated = current.includes(jobType)
      ? current.filter(t => t !== jobType)
      : [...current, jobType]
    setValue('job_types', updated, { shouldDirty: true })
  }

  const jobTypeOptions = [
    { value: 'full-time', label: 'Full-time' },
    { value: 'part-time', label: 'Part-time' },
    { value: 'contract', label: 'Contract' },
    { value: 'internship', label: 'Internship' },
  ]

  const remoteOptions = [
    { value: 'remote', label: 'Remote Only' },
    { value: 'hybrid', label: 'Hybrid' },
    { value: 'onsite', label: 'On-site Only' },
    { value: 'no-preference', label: 'No Preference' },
  ]

  if (isLoading) {
    return (
      <div className="space-y-8">
        <div>
          <Skeleton className="h-8 w-48 mb-2" />
          <Skeleton className="h-4 w-96" />
        </div>
        <div className="grid gap-6 lg:grid-cols-2">
          {[...Array(4)].map((_, i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-6 w-32" />
                <Skeleton className="h-4 w-48" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-32 w-full" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
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
            <h1 className="text-3xl font-bold">Job Preferences</h1>
            <p className="text-muted-foreground mt-2">
              Configure your job search criteria to get better matches
            </p>
          </div>
          <Button 
            onClick={handleSubmit(onSubmit)}
            disabled={!isDirty || updateMutation.isPending}
          >
            <Save className="mr-2 h-4 w-4" />
            {updateMutation.isPending ? 'Saving...' : 'Save Changes'}
          </Button>
        </div>
      </motion.div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Role Preferences */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
          >
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Briefcase className="h-5 w-5" />
                  <span>Role Preferences</span>
                </CardTitle>
                <CardDescription>
                  What type of role are you looking for?
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="text-sm font-medium">Desired Role</label>
                  <Input
                    {...register('desired_role')}
                    placeholder="e.g., Software Engineer, Product Manager"
                    className="mt-1"
                  />
                </div>

                <div>
                  <label className="text-sm font-medium">Job Types</label>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {jobTypeOptions.map((option) => (
                      <Badge
                        key={option.value}
                        variant={watchedJobTypes.includes(option.value) ? "default" : "outline"}
                        className="cursor-pointer"
                        onClick={() => toggleJobType(option.value)}
                      >
                        {option.label}
                      </Badge>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="text-sm font-medium">Remote Preference</label>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {remoteOptions.map((option) => (
                      <Badge
                        key={option.value}
                        variant={watch('remote_preference') === option.value ? "default" : "outline"}
                        className="cursor-pointer"
                        onClick={() => setValue('remote_preference', option.value, { shouldDirty: true })}
                      >
                        {option.label}
                      </Badge>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Location Preferences */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <MapPin className="h-5 w-5" />
                  <span>Location Preferences</span>
                </CardTitle>
                <CardDescription>
                  Where would you like to work?
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="text-sm font-medium">Add Location</label>
                  <div className="flex space-x-2 mt-1">
                    <Input
                      value={newLocation}
                      onChange={(e) => setNewLocation(e.target.value)}
                      placeholder="e.g., San Francisco, CA"
                      onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addLocation())}
                    />
                    <Button type="button" onClick={addLocation} size="sm">
                      <Plus className="h-4 w-4" />
                    </Button>
                  </div>
                </div>

                <div>
                  <label className="text-sm font-medium">Preferred Locations</label>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {watchedLocations.map((location) => (
                      <Badge key={location} variant="secondary" className="flex items-center space-x-1">
                        <span>{location}</span>
                        <button
                          type="button"
                          onClick={() => removeLocation(location)}
                          className="ml-1 hover:text-destructive"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </Badge>
                    ))}
                  </div>
                  {watchedLocations.length === 0 && (
                    <p className="text-sm text-muted-foreground mt-2">
                      No locations added yet
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Salary Preferences */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
          >
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <DollarSign className="h-5 w-5" />
                  <span>Salary Expectations</span>
                </CardTitle>
                <CardDescription>
                  What&apos;s your expected salary range?
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium">Minimum Salary</label>
                    <Input
                      {...register('salary_min', { valueAsNumber: true })}
                      type="number"
                      placeholder="50000"
                      className="mt-1"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium">Maximum Salary</label>
                    <Input
                      {...register('salary_max', { valueAsNumber: true })}
                      type="number"
                      placeholder="100000"
                      className="mt-1"
                    />
                  </div>
                </div>
                <p className="text-xs text-muted-foreground">
                  Leave blank if you prefer not to specify salary requirements
                </p>
              </CardContent>
            </Card>
          </motion.div>

          {/* Skills */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
          >
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Settings className="h-5 w-5" />
                  <span>Skills & Technologies</span>
                </CardTitle>
                <CardDescription>
                  What skills do you want to use in your next role?
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="text-sm font-medium">Add Skill</label>
                  <div className="flex space-x-2 mt-1">
                    <Input
                      value={newSkill}
                      onChange={(e) => setNewSkill(e.target.value)}
                      placeholder="e.g., React, Python, AWS"
                      onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addSkill())}
                    />
                    <Button type="button" onClick={addSkill} size="sm">
                      <Plus className="h-4 w-4" />
                    </Button>
                  </div>
                </div>

                <div>
                  <label className="text-sm font-medium">Your Skills</label>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {watchedSkills.map((skill) => (
                      <Badge key={skill} variant="secondary" className="flex items-center space-x-1">
                        <span>{skill}</span>
                        <button
                          type="button"
                          onClick={() => removeSkill(skill)}
                          className="ml-1 hover:text-destructive"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </Badge>
                    ))}
                  </div>
                  {watchedSkills.length === 0 && (
                    <p className="text-sm text-muted-foreground mt-2">
                      No skills added yet
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Save Button */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.5 }}
          className="flex justify-end"
        >
          <Button 
            type="submit"
            disabled={!isDirty || updateMutation.isPending}
            size="lg"
          >
            <Save className="mr-2 h-4 w-4" />
            {updateMutation.isPending ? 'Saving...' : 'Save Preferences'}
          </Button>
        </motion.div>
      </form>
    </div>
  )
}