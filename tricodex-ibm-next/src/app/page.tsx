"use client"

import { useEffect, useState, useCallback } from "react"
import { AppSidebar } from "@/components/app-sidebar"
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb"
import { Separator } from "@/components/ui/separator"
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar"
import { FileUpload } from "@/components/ui/file-upload"
import { useAnimatedText } from "@/components/ui/animated-text"
import { Button } from "@/components/ui/button"
import { 
  Bot,
  FileText,
  TimerIcon,
  Activity,
  Users,
  Download,
  RefreshCw
} from "lucide-react"
import { ProcessMetrics } from "@/components/process/process-metrics"
import { ProcessPatterns } from "@/components/process/process-patterns"
import { ResourceAnalysis } from "@/components/process/resource-analysis"
import { AnalysisPDF } from "@/components/process/analysis-pdf"
import { pdf } from '@react-pdf/renderer'
import { saveAs } from 'file-saver'
import { startAnalysis, checkAnalysisStatus } from "@/lib/api"

// Define types for our data structures
type ThoughtMessage = {
  timestamp: string
  stage: string
  thought: string
  progress: number
}

type AnalysisResult = {
  task_id: string
  status: "processing" | "completed" | "failed"
  progress: number
  thoughts: ThoughtMessage[]
  results?: {
    structure: any
    patterns: any[]
    performance: any
    improvements: any
    synthesis: any
  }
}

export default function ProcessLensPage() {
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null)
  const [activeSection, setActiveSection] = useState<string>("upload")
  const [isPolling, setIsPolling] = useState(false)

  const currentThought = analysisResult?.thoughts?.[analysisResult.thoughts.length - 1]?.thought || ""
  const animatedThought = useAnimatedText(currentThought, " ")

  const handleFileUpload = async (files: File[]) => {
    if (!files.length) return

    const formData = new FormData()
    formData.append("file", files[0])
    formData.append("project_name", "Process Analysis " + new Date().toLocaleDateString())

    try {
      const data = await startAnalysis(formData)
      setAnalysisResult({
        task_id: data.task_id,
        status: "processing",
        progress: 0,
        thoughts: []
      })
      setIsPolling(true)
      setActiveSection("analysis")
    } catch (error) {
      console.error("Upload error:", error)
    }
  }

  const pollStatus = useCallback(async () => {
    if (!analysisResult?.task_id || !isPolling) return

    try {
      const data = await checkAnalysisStatus(analysisResult.task_id)
      setAnalysisResult(data)
      
      if (data.status === "completed" || data.status === "failed") {
        setIsPolling(false)
      }
    } catch (error) {
      console.error("Polling error:", error)
      setIsPolling(false)
    }
  }, [analysisResult?.task_id, isPolling])

  useEffect(() => {
    let interval: NodeJS.Timeout
    if (isPolling) {
      interval = setInterval(pollStatus, 2000)
    }
    return () => clearInterval(interval)
  }, [isPolling, pollStatus])

  const handleDownloadPDF = async () => {
    if (!analysisResult) return
    
    try {
      const blob = await pdf(<AnalysisPDF data={analysisResult} />).toBlob()
      saveAs(blob, `process-analysis-${new Date().toISOString()}.pdf`)
    } catch (error) {
      console.error("PDF generation error:", error)
    }
  }

  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset>
        <header className="flex h-16 shrink-0 items-center gap-2 border-b">
          <div className="flex items-center gap-2 px-4 w-full justify-between">
            <div className="flex items-center gap-2">
              <SidebarTrigger className="-ml-1" />
              <Separator orientation="vertical" className="mr-2 h-4" />
              <Breadcrumb>
                <BreadcrumbList>
                  <BreadcrumbItem>
                    <BreadcrumbPage>Process Mining</BreadcrumbPage>
                  </BreadcrumbItem>
                  <BreadcrumbSeparator />
                  <BreadcrumbItem>
                    <BreadcrumbPage>{activeSection === "upload" ? "Upload" : "Analysis"}</BreadcrumbPage>
                  </BreadcrumbItem>
                </BreadcrumbList>
              </Breadcrumb>
            </div>
            {analysisResult?.status === "completed" && (
              <Button onClick={handleDownloadPDF} variant="outline">
                <Download className="mr-2 h-4 w-4" />
                Download Report
              </Button>
            )}
          </div>
        </header>

        <main className="flex flex-1 flex-col gap-4 p-4 max-w-7xl mx-auto w-full">
          {activeSection === "upload" ? (
            <div className="mt-8">
              <FileUpload onChange={handleFileUpload} />
            </div>
          ) : (
            <div className="grid gap-6">
              {/* Progress Section */}
              <div className="rounded-lg border bg-card p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold">Analysis Progress</h2>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-muted-foreground">
                      {analysisResult?.progress || 0}%
                    </span>
                    {isPolling && (
                      <RefreshCw className="h-4 w-4 animate-spin" />
                    )}
                  </div>
                </div>
                <div className="h-2 w-full bg-secondary rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary transition-all duration-500"
                    style={{ width: `${analysisResult?.progress || 0}%` }}
                  />
                </div>
              </div>

              {/* Thoughts Stream */}
              <div className="rounded-lg border bg-card p-6">
                <h2 className="text-lg font-semibold mb-4">Analysis Thoughts</h2>
                <div className="space-y-4 max-h-[400px] overflow-y-auto">
                  {analysisResult?.thoughts.map((thought, index) => (
                    <div
                      key={index}
                      className="flex items-start gap-4 p-4 rounded-lg bg-muted/50"
                    >
                      <Bot className="h-6 w-6 text-primary" />
                      <div className="flex-1">
                        <div className="text-sm text-muted-foreground mb-1">
                          {new Date(thought.timestamp).toLocaleTimeString()}
                        </div>
                        <div className="text-sm">{thought.thought}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Results Sections - Only show when complete */}
              {analysisResult?.status === "completed" && (
                <div className="grid gap-6 md:grid-cols-2">
                  <div className="rounded-lg border bg-card p-6">
                    <div className="flex items-center gap-2 mb-4">
                      <Activity className="h-5 w-5 text-primary" />
                      <h2 className="text-lg font-semibold">Performance Metrics</h2>
                    </div>
                    <ProcessMetrics data={analysisResult.results} />
                  </div>

                  <div className="rounded-lg border bg-card p-6">
                    <div className="flex items-center gap-2 mb-4">
                      <TimerIcon className="h-5 w-5 text-primary" />
                      <h2 className="text-lg font-semibold">Process Patterns</h2>
                    </div>
                    <ProcessPatterns data={analysisResult.results} />
                  </div>

                  <div className="rounded-lg border bg-card p-6">
                    <div className="flex items-center gap-2 mb-4">
                      <Users className="h-5 w-5 text-primary" />
                      <h2 className="text-lg font-semibold">Resource Analysis</h2>
                    </div>
                    <ResourceAnalysis data={analysisResult.results} />
                  </div>

                  <div className="rounded-lg border bg-card p-6">
                    <div className="flex items-center gap-2 mb-4">
                      <FileText className="h-5 w-5 text-primary" />
                      <h2 className="text-lg font-semibold">Recommendations</h2>
                    </div>
                    <div className="space-y-4">
                      {analysisResult.results?.improvements?.map((improvement: any, index: number) => (
                        <div key={index} className="p-4 rounded-lg bg-muted/50">
                          <div className="font-medium mb-2">{improvement.action}</div>
                          <div className="text-sm text-muted-foreground">
                            Expected Impact: {improvement.expected_impact}%
                          </div>
                          <div className="text-sm text-muted-foreground">
                            Implementation: {improvement.implementation_complexity} days
                          </div>
                          <div className="text-sm mt-2">{improvement.suggestion}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </main>
      </SidebarInset>
    </SidebarProvider>
  )
}
