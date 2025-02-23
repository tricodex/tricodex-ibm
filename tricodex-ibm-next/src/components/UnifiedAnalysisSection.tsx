import { useState, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import type { AnalysisResult, AnalysisSectionProps } from "@/types"
import { ThoughtBubble } from '@/components/ui/ThoughtBubble'
import {
  Bot,
  FileText,
  Timer,
  Activity,
  Users,
  Download,
  RefreshCw,
  ArrowRight,
  CheckCircle2,
  XCircle
} from "lucide-react"
import { TextShimmer } from "@/components/ui/text-shimmer"
import { ProcessMetrics } from "@/components/process/process-metrics"
import { ProcessPatterns } from "@/components/process/process-patterns"
import { ResourceAnalysis } from "@/components/process/resource-analysis"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

export const UnifiedAnalysisSection = ({
  analysisResult,
  isPolling,
  onDownloadPDF,
  type = 'watson'
}: AnalysisSectionProps) => {
  const [showMetrics, setShowMetrics] = useState(false);
  const isProcessing = isPolling || analysisResult?.status === "processing";
  
  const loadingState = !analysisResult ? 'initial' :
    isProcessing ? 'processing' :
    analysisResult.status === 'failed' ? 'error' :
    'complete';

  useEffect(() => {
    if (analysisResult?.status === "completed") {
      const timer = setTimeout(() => setShowMetrics(true), 500);
      return () => clearTimeout(timer);
    }
  }, [analysisResult?.status]);

  return (
    <div className="space-y-8">
      {/* Status Header */}
      <div className={cn(
        "rounded-lg border p-6",
        loadingState === 'error' ? "bg-destructive/10" : 
        type === 'watson' ? "bg-blue-50" : "bg-emerald-50"
      )}>
        <div className="flex items-center justify-between mb-4">
          <TextShimmer as="h2" className={cn(
            "text-lg font-semibold",
            loadingState === 'error' ? "text-destructive" :
            type === 'watson' ? "text-blue-700" : "text-emerald-700"
          )}>
            {`${type === 'watson' ? 'Watson' : 'Gemini'} Analysis ${
              loadingState === 'initial' ? 'Ready' :
              loadingState === 'processing' ? 'In Progress' :
              loadingState === 'error' ? 'Error' : 'Complete'
            }`}
          </TextShimmer>
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">
              {analysisResult?.progress || 0}%
            </span>
            {isProcessing && (
              <RefreshCw className="h-4 w-4 animate-spin text-primary" />
            )}
          </div>
        </div>

        {/* Progress Bar */}
        <div className="relative h-2 w-full bg-muted rounded-full overflow-hidden">
          <div
            className={cn(
              "absolute inset-0 transition-all duration-500 ease-out",
              loadingState === 'error' ? "bg-destructive" :
              type === 'watson' ? "bg-blue-500" : "bg-emerald-500",
              loadingState === 'processing' && "animate-pulse"
            )}
            style={{ width: `${analysisResult?.progress || 0}%` }}
          />
          {isProcessing && (
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/25 to-transparent animate-shimmer" />
          )}
        </div>

        {/* Error Display */}
        {analysisResult?.error && (
          <div className="mt-4 text-destructive">
            <div className="flex items-center gap-2">
              <XCircle className="h-5 w-5" />
              <p className="font-medium">Analysis Error</p>
            </div>
            <p className="mt-2 text-sm">{analysisResult.error}</p>
          </div>
        )}
      </div>

      {/* Analysis Progress */}
      <div className="rounded-lg border bg-card p-6">
        <h3 className="text-lg font-semibold mb-4">Analysis Progress</h3>
        <div className="space-y-2 max-h-[400px] overflow-y-auto">
          <AnimatePresence>
            {analysisResult?.thoughts.map((thought, index) => (
              <ThoughtBubble
                key={thought.timestamp}
                thought={thought.thought}
                timestamp={thought.timestamp}
                type={type}
                isActive={index === analysisResult.thoughts.length - 1}
              />
            ))}
          </AnimatePresence>
        </div>
      </div>

      {/* Results Display */}
      {analysisResult?.status === "completed" && analysisResult.results && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-6"
        >
          {/* Insights Section */}
          {analysisResult.results.synthesis?.insights?.length > 0 && (
            <div className="rounded-lg border bg-card p-6">
              <h3 className="text-lg font-semibold mb-4">Key Insights</h3>
              <div className="space-y-2">
                {analysisResult.results.synthesis.insights.map((insight, index) => (
                  <div key={index} className="p-3 rounded-lg bg-muted/50">
                    {insight}
                  </div>
                ))}
              </div>
            </div>
          )}

          <div 
            className={cn(
              "grid gap-6 md:grid-cols-2 transition-all duration-500",
              showMetrics ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
            )}
          >
            {/* Performance Metrics */}
            <div className="rounded-lg border bg-card p-6">
              <div className="flex items-center gap-2 mb-4">
                <Activity className="h-5 w-5 text-primary" />
                <h3 className="text-lg font-semibold">Performance Metrics</h3>
              </div>
              <ProcessMetrics data={analysisResult.results} />
            </div>

            {/* Process Patterns */}
            <div className="rounded-lg border bg-card p-6">
              <div className="flex items-center gap-2 mb-4">
                <Timer className="h-5 w-5 text-primary" />
                <h3 className="text-lg font-semibold">Process Patterns</h3>
              </div>
              <ProcessPatterns data={analysisResult.results} />
            </div>

            {/* Resource Analysis */}
            <div className="rounded-lg border bg-card p-6">
              <div className="flex items-center gap-2 mb-4">
                <Users className="h-5 w-5 text-primary" />
                <h3 className="text-lg font-semibold">Resource Analysis</h3>
              </div>
              <ResourceAnalysis data={analysisResult.results} />
            </div>

            {/* Improvements Section */}
            {analysisResult.results.improvements?.length > 0 && (
              <div className="rounded-lg border bg-card p-6">
                <div className="flex items-center gap-2 mb-4">
                  <FileText className="h-5 w-5 text-primary" />
                  <h3 className="text-lg font-semibold">Recommendations</h3>
                </div>
                <div className="space-y-4">
                  {analysisResult.results.improvements.map((improvement, index) => (
                    <div 
                      key={index}
                      className="p-4 rounded-lg bg-muted/50 transition-all duration-300 hover:bg-muted"
                    >
                      <div className="flex items-center gap-2">
                        <ArrowRight className="h-4 w-4 text-primary" />
                        <div className="font-medium">{improvement.action}</div>
                      </div>
                      <div className="mt-2 space-y-1 text-sm text-muted-foreground">
                        <div>Expected Impact: {improvement.expected_impact}%</div>
                        <div>Implementation: {improvement.implementation_complexity} days</div>
                      </div>
                      <div className="text-sm mt-2">{improvement.suggestion}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </motion.div>
      )}
    </div>
  );
};