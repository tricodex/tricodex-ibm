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
import { AnalysisSection } from "@/components/AnalysisSection"
import { GeminiAnalysisSection } from "@/components/GeminiAnalysisSection"

export default function ProcessLensPage() {
  const [taskId, setTaskId] = useState<string | null>(null)
  const [activeSection, setActiveSection] = useState<string>("upload")
  
  // Use the WebSocket hook
  const { isConnected, error, thoughts, results, latestThought } = useAnalysisSocket(taskId, 'watson')
  const { 
    isConnected: geminiConnected, 
    error: geminiError, 
    thoughts: geminiThoughts, 
    results: geminiResults,
    latestThought: geminiLatestThought 
  } = useAnalysisSocket(taskId, 'gemini')

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
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* WatsonX Analysis */}
              <AnalysisSection
                analysisResult={results}
                isPolling={isConnected}
                onDownloadPDF={handleDownloadPDF}
              />
              
              {/* Gemini Analysis */}
              <GeminiAnalysisSection
                analysisResult={geminiResults}
                isPolling={geminiConnected}
                onDownloadPDF={handleDownloadPDF}
              />
            </div>
          )}
        </main>
      </SidebarInset>
    </SidebarProvider>
  )
}