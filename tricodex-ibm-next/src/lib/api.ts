import { type AnalysisResult } from "@/types"

export const runtime = "edge"

// API configuration
export const API_CONFIG = {
  baseUrl: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  endpoints: {
    health: "/health",
    analyze: "/analyze",
    status: (taskId: string) => `/status/${taskId}`,
    projects: "/projects",
    timing: "/analyze/timing",
    quality: "/analyze/quality",
    resources: "/analyze/resources",
  }
}

// API client functions
export async function startAnalysis(formData: FormData) {
  const response = await fetch(`${API_CONFIG.baseUrl}${API_CONFIG.endpoints.analyze}`, {
    method: "POST",
    body: formData,
  })
  return response.json()
}

export async function checkAnalysisStatus(taskId: string): Promise<AnalysisResult> {
  const response = await fetch(
    `${API_CONFIG.baseUrl}${API_CONFIG.endpoints.status(taskId)}`
  )
  return response.json()
}

export async function getProjects(skip = 0, limit = 10) {
  const response = await fetch(
    `${API_CONFIG.baseUrl}${API_CONFIG.endpoints.projects}?skip=${skip}&limit=${limit}`
  )
  return response.json()
}

export async function checkHealth() {
  const response = await fetch(`${API_CONFIG.baseUrl}${API_CONFIG.endpoints.health}`)
  return response.json()
}