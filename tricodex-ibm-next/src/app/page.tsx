"use client"

import { useState, useEffect } from "react"
import { AppSidebar } from "@/components/app-sidebar"
import {
  Breadcrumb,
  BreadcrumbItem,
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
import { Button } from "@/components/ui/button"
import { 
  Bot,
  FileText,
  TimerIcon,
  Activity,
  Users,
  Download,
} from "lucide-react"
import { ProcessMetrics } from "@/components/process/process-metrics"
import { ProcessPatterns } from "@/components/process/process-patterns"
import { ResourceAnalysis } from "@/components/process/resource-analysis"
import { AnalysisPDF } from "@/components/process/analysis-pdf"
import { pdf } from '@react-pdf/renderer'
import { saveAs } from 'file-saver'
import { startAnalysis } from "@/lib/api"
import { toast } from 'sonner'
import { Toaster } from 'sonner'
import { useAnalysisSocket } from "@/hooks/useAnalysisSocket"

export default function ProcessLensPage() {
  const [taskId, setTaskId] = useState<string | null>(null)
  const [activeSection, setActiveSection] = useState<string>("upload")
  
  // Use the WebSocket hook
  const { isConnected, error, thoughts, results, latestThought } = useAnalysisSocket(taskId)

  const handleFileUpload = async (files: File[]) => {
    if (!files.length) return

    setActiveSection("analysis") // Update UI immediately to show analysis view

    const formData = new FormData()
    formData.append("file", files[0])
    formData.append("project_name", "Process Analysis " + new Date().toLocaleDateString())

    try {
      await toast.promise(
        startAnalysis(formData).then(data => {
          setTaskId(data.task_id)
          return data
        }),
        {
          loading: 'Starting analysis...',
          success: (data) => `Analysis started successfully - Task ID: ${data.task_id}`,
          error: (err) => {
            console.error("Upload error:", err)
            setActiveSection("upload") // Reset on error
            return err.message || 'Failed to start analysis'
          }
        }
      )
    } catch (error) {
      console.error("Upload error:", error)
      toast.error('Failed to upload file')
      setActiveSection("upload")
    }
  }

  const handleDownloadPDF = async () => {
    if (!results) return
    
    try {
      await toast.promise(
        pdf(<AnalysisPDF data={{ 
          thoughts, 
          results,
          status: results ? 'completed' : 'processing',
          progress: results ? 100 : latestThought?.progress || 0,
          task_id: taskId || ''
        }} />).toBlob().then(blob => {
          saveAs(blob, `process-analysis-${new Date().toISOString()}.pdf`)
        }),
        {
          loading: 'Generating PDF...',
          success: 'PDF downloaded successfully',
          error: 'Failed to generate PDF'
        }
      )
    } catch (error) {
      console.error("PDF generation error:", error)
      toast.error('Failed to generate PDF')
    }
  }

  // Display error toast when WebSocket error occurs
  useEffect(() => {
    if (error) {
      toast.error(error)
    }
  }, [error])

  return (
    <SidebarProvider>
      <Toaster />
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
            {results && (
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
              {/* Connection Status */}
              <div className="flex items-center gap-2">
                <div 
                  className={`h-2 w-2 rounded-full ${
                    isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'
                  }`} 
                />
                <span className="text-sm text-muted-foreground">
                  {isConnected ? 'Processing Analysis...' : error ? 'Connection Error' : 'Analysis Complete'}
                </span>
              </div>

              {/* Error Display */}
              {error && (
                <div className="rounded-lg border border-destructive bg-destructive/10 p-4 text-destructive">
                  {error}
                  <Button 
                    variant="outline" 
                    className="mt-2"
                    onClick={() => window.location.reload()}
                  >
                    Retry
                  </Button>
                </div>
              )}

              {/* Progress Section */}
              <div className="rounded-lg border bg-card p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold">Analysis Progress</h2>
                  <span className="text-sm text-muted-foreground">
                    {latestThought?.progress || 0}%
                  </span>
                </div>
                <div className="h-2 w-full bg-secondary rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary transition-all duration-500"
                    style={{ width: `${latestThought?.progress || 0}%` }}
                  >
                    {isConnected && (
                      <div className="h-full w-full animate-pulse bg-primary/50" />
                    )}
                  </div>
                </div>
              </div>

              {/* Thoughts Stream */}
              <div className="rounded-lg border bg-card p-6">
                <h2 className="text-lg font-semibold mb-4">Analysis Thoughts</h2>
                <div className="space-y-4 max-h-[400px] overflow-y-auto">
                  {thoughts.map((thought, index) => (
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
              {results && (
                <div className="grid gap-6 md:grid-cols-2">
                  <div className="rounded-lg border bg-card p-6">
                    <div className="flex items-center gap-2 mb-4">
                      <Activity className="h-5 w-5 text-primary" />
                      <h2 className="text-lg font-semibold">Performance Metrics</h2>
                    </div>
                    <ProcessMetrics data={results} />
                  </div>

                  <div className="rounded-lg border bg-card p-6">
                    <div className="flex items-center gap-2 mb-4">
                      <TimerIcon className="h-5 w-5 text-primary" />
                      <h2 className="text-lg font-semibold">Process Patterns</h2>
                    </div>
                    <ProcessPatterns data={results} />
                  </div>

                  <div className="rounded-lg border bg-card p-6">
                    <div className="flex items-center gap-2 mb-4">
                      <Users className="h-5 w-5 text-primary" />
                      <h2 className="text-lg font-semibold">Resource Analysis</h2>
                    </div>
                    <ResourceAnalysis data={results} />
                  </div>

                  <div className="rounded-lg border bg-card p-6">
                    <div className="flex items-center gap-2 mb-4">
                      <FileText className="h-5 w-5 text-primary" />
                      <h2 className="text-lg font-semibold">Recommendations</h2>
                    </div>
                    <div className="space-y-4">
                      {results?.improvements?.map((improvement: any, index: number) => (
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