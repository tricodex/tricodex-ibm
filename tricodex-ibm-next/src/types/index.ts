export type ProcessMetric = {
  value: number
  label: string
  unit: string
}

export type ProcessPattern = {
  name: string
  frequency: number
  performance_metrics: {
    avg_duration?: number
    business_impact?: number
  }
}

export type ProcessImprovement = {
  action: string
  expected_impact: number
  implementation_complexity: number
  suggestion: string
}

export type ThoughtMessage = {
  timestamp: string
  stage: string
  thought: string
  progress: number
}

export type AnalysisResult = {
  task_id: string
  status: "processing" | "completed" | "failed"
  progress: number
  thoughts: ThoughtMessage[]
  results?: {
    structure: Record<string, any>
    patterns: ProcessPattern[]
    performance: {
      timing: Record<string, number>
      quality: Record<string, number>
      resources: Record<string, any>
    }
    improvements: ProcessImprovement[]
    synthesis: Record<string, any>
  }
}