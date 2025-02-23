"use client"

import { useState } from "react"
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
import { Download } from "lucide-react"
import { AnalysisPDF } from "@/components/process/analysis-pdf"
import { pdf } from '@react-pdf/renderer'
import { saveAs } from 'file-saver'
import { api } from "@/lib/api"
import { toast } from 'sonner'
import { Toaster } from 'sonner'
import { useProcessLensSocket } from "@/hooks/useProcessLensSocket"
import { UnifiedAnalysisSection } from "@/components/UnifiedAnalysisSection"

export default function ProcessLensPage() {
  const [taskId, setTaskId] = useState<string | null>(null)
  const [activeSection, setActiveSection] = useState<string>("upload")
  
  const { 
    status, 
    error, 
    thoughts = [], 
    results,
    latestThought,
    isConnected 
  } = useProcessLensSocket({ taskId });

  const handleFileUpload = async (files: File[]) => {
    if (!files.length) return

    setActiveSection("analysis")

    const file = files[0]
    const projectName = "Process Analysis " + new Date().toLocaleDateString()

    try {
      await toast.promise(
        api.startAnalysis(file, projectName).then(data => {
          setTaskId(data.task_id)
          return data
        }),
        {
          loading: 'Starting analysis...',
          success: (data) => `Analysis started successfully - Task ID: ${data.task_id}`,
          error: (err) => {
            console.error("Upload error:", err)
            setActiveSection("upload")
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
          taskId: taskId || '',
          status: results ? 'completed' : 'processing',
          progress: results ? 100 : latestThought?.progress || 0,
          thoughts: thoughts,
          results: results,
          error: error
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
              <UnifiedAnalysisSection
                analysisResult={results ? {
                  taskId: taskId || '',
                  status: results ? 'completed' : 'processing',
                  progress: latestThought?.progress || 0,
                  thoughts: thoughts,
                  results: results,
                  error: error
                } : null}
                isPolling={isConnected}
                onDownloadPDF={handleDownloadPDF}
                type="watson"
              />
              
              <UnifiedAnalysisSection
                analysisResult={results ? {
                  taskId: taskId || '',
                  status: results ? 'completed' : 'processing',
                  progress: latestThought?.progress || 0,
                  thoughts: thoughts,
                  results: results,
                  error: error
                } : null}
                isPolling={isConnected}
                onDownloadPDF={handleDownloadPDF}
                type="gemini"
              />
            </div>
          )}
        </main>
      </SidebarInset>
    </SidebarProvider>
  );
}