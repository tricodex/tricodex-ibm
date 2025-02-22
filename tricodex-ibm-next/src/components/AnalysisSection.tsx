import { useState, useCallback, useEffect } from "react"
import { AnimatedThoughts } from "@/components/ui/animated-thoughts"
import {
  Bot,
  FileText,
  Timer,
  Activity,
  Users,
  Download,
  RefreshCw,
  ArrowRight
} from "lucide-react"
import { TextShimmer } from "@/components/ui/text-shimmer"
import { ProcessMetrics } from "@/components/process/process-metrics"
import { ProcessPatterns } from "@/components/process/process-patterns"
import { ResourceAnalysis } from "@/components/process/resource-analysis"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface Improvement {
  action: string;
  expected_impact: number;
  implementation_complexity: number;
  suggestion: string;
}

interface AnalysisResults {
  performance: any;
  patterns: any[];
  improvements: Improvement[];
}

interface AnalysisResult {
  status: "processing" | "completed" | "failed";
  progress: number;
  thoughts: Array<{
    timestamp: string;
    stage: string;
    thought: string;
    progress: number;
  }>;
  results?: AnalysisResults;
}

interface AnalysisSectionProps {
  analysisResult: AnalysisResult | null;
  isPolling: boolean;
  onDownloadPDF: () => void;
}

export const AnalysisSection = ({
  analysisResult,
  isPolling,
  onDownloadPDF
}: AnalysisSectionProps) => {
  const isProcessing = isPolling || analysisResult?.status === "processing";
  const [showMetrics, setShowMetrics] = useState(false);

  useEffect(() => {
    if (analysisResult?.status === "completed") {
      const timer = setTimeout(() => setShowMetrics(true), 500);
      return () => clearTimeout(timer);
    }
  }, [analysisResult?.status]);

  return (
    <div className="space-y-8">
      {/* Progress Header */}
      <div className="rounded-lg border bg-card p-6">
        <div className="flex items-center justify-between mb-4">
          <TextShimmer as="h2" className="text-lg font-semibold">
            Analysis Progress
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
        
        {/* Animated Progress Bar */}
        <div className="relative h-2 w-full bg-muted rounded-full overflow-hidden">
          <div
            className="absolute inset-0 bg-primary transition-all duration-500 ease-out"
            style={{ width: `${analysisResult?.progress || 0}%` }}
          />
          {isProcessing && (
            <div
              className="absolute inset-0 bg-primary/30 animate-[shimmer_2s_infinite]"
              style={{
                backgroundImage: 'linear-gradient(90deg, transparent, hsl(var(--primary)/0.4), transparent)',
                backgroundSize: '200% 100%',
                backgroundPosition: '200% 0',
              }}
            />
          )}
        </div>
      </div>

      {/* Thoughts Stream */}
      <div className="rounded-lg border bg-card p-6">
        <AnimatedThoughts 
          thoughts={analysisResult?.thoughts || []} 
          isProcessing={isProcessing}
        />
      </div>

      {/* Results Sections */}
      {analysisResult?.status === "completed" && analysisResult.results && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <TextShimmer as="h2" className="text-lg font-semibold">
              Analysis Results
            </TextShimmer>
            <Button onClick={onDownloadPDF} variant="outline">
              <Download className="mr-2 h-4 w-4" />
              Download Report
            </Button>
          </div>

          <div 
            className={cn(
              "grid gap-6 md:grid-cols-2 transition-all duration-500",
              showMetrics ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
            )}
          >
            {/* Performance Metrics Card */}
            <div className="rounded-lg border bg-card p-6 transition-all duration-500 hover:shadow-lg">
              <div className="flex items-center gap-2 mb-4">
                <Activity className="h-5 w-5 text-primary" />
                <h3 className="text-lg font-semibold">Performance Metrics</h3>
              </div>
              <ProcessMetrics data={analysisResult.results} />
            </div>

            {/* Process Patterns Card */}
            <div className="rounded-lg border bg-card p-6 transition-all duration-500 hover:shadow-lg">
              <div className="flex items-center gap-2 mb-4">
                <Timer className="h-5 w-5 text-primary" />
                <h3 className="text-lg font-semibold">Process Patterns</h3>
              </div>
              <ProcessPatterns data={analysisResult.results} />
            </div>

            {/* Resource Analysis Card */}
            <div className="rounded-lg border bg-card p-6 transition-all duration-500 hover:shadow-lg">
              <div className="flex items-center gap-2 mb-4">
                <Users className="h-5 w-5 text-primary" />
                <h3 className="text-lg font-semibold">Resource Analysis</h3>
              </div>
              <ResourceAnalysis data={analysisResult.results} />
            </div>

            {/* Recommendations Card */}
            <div className="rounded-lg border bg-card p-6 transition-all duration-500 hover:shadow-lg">
              <div className="flex items-center gap-2 mb-4">
                <FileText className="h-5 w-5 text-primary" />
                <h3 className="text-lg font-semibold">Recommendations</h3>
              </div>
              <div className="space-y-4">
                {analysisResult.results.improvements?.map((improvement: Improvement, index: number) => (
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
          </div>
        </div>
      )}
    </div>
  );
};