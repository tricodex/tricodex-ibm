import { useState, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import type { AnalysisResult, ThoughtMessage } from "@/types/analysis"
import { AnimatedThoughts } from "@/components/ui/animated-thoughts"
import { TextShimmer } from "@/components/ui/text-shimmer"
import { ProcessMetrics } from "@/components/process/process-metrics"
import { ProcessPatterns } from "@/components/process/process-patterns"
import { ResourceAnalysis } from "@/components/process/resource-analysis"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { ThoughtBubble } from '@/components/ui/ThoughtBubble'

interface GeminiAnalysisSectionProps {
  analysisResult: AnalysisResult | null;
  isPolling: boolean;
  onDownloadPDF: () => void;
}

export const GeminiAnalysisSection = ({
  analysisResult,
  isPolling,
  onDownloadPDF
}: GeminiAnalysisSectionProps) => {
  const [showMetrics, setShowMetrics] = useState(false);

  // Similar structure to AnalysisSection but with Gemini-specific styling
  const loadingState = !analysisResult ? 'initial' :
    isPolling ? 'processing' :
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
      <div className="rounded-lg border bg-emerald-50 p-6">
        <div className="flex items-center justify-between mb-4">
          <TextShimmer as="h2" className="text-lg font-semibold text-emerald-700">
            {`Gemini Analysis ${loadingState === 'initial' ? 'Ready' : 
              loadingState === 'processing' ? 'In Progress' :
              loadingState === 'error' ? 'Error' : 'Complete'}`}
          </TextShimmer>
          {/* Rest of the component similar to AnalysisSection but with Gemini theming */}
        </div>
        {/* ...Progress bar and other sections similar to AnalysisSection... */}
      </div>
      <div className="rounded-lg border bg-card p-6">
        <h3 className="text-lg font-semibold mb-4">Gemini Analysis Progress</h3>
        <div className="space-y-2 max-h-[400px] overflow-y-auto">
          <AnimatePresence>
            {analysisResult?.thoughts.map((thought: ThoughtMessage, index: number) => (
              <ThoughtBubble
                key={thought.timestamp}
                thought={thought.thought}
                timestamp={thought.timestamp}
                type="gemini"
                isActive={index === analysisResult.thoughts.length - 1}
              />
            ))}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
};
