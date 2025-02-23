// Shared message types
export interface ThoughtMessage {
  timestamp: string;
  stage?: string;
  thought: string;
  progress: number;
}

// Core metric and analysis types
export interface ProcessMetric {
  value: number;
  label: string;
  unit: string;
}

export interface ProcessPattern {
  name: string;
  frequency: number;
  description?: string;
  type?: string;
  confidence?: number;
  performance_metrics?: {
    avg_duration?: number;
    business_impact?: number;
  };
}

export interface ProcessImprovement {
  action: string;
  expected_impact: number;
  implementation_complexity: number;
  suggestion: string;
}

// Analysis result types
export interface AnalysisSynthesis {
  insights: string[];
  recommendations: string[];
  metrics: Record<string, ProcessMetric>;
}

export interface AnalysisPerformance {
  timing: Record<string, number>;
  quality: Record<string, number>;
  resources: Record<string, any>;
}

export interface AnalysisResults {
  structure: Record<string, any>;
  patterns: ProcessPattern[];
  performance: AnalysisPerformance;
  improvements: ProcessImprovement[];
  synthesis: AnalysisSynthesis;
  data_quality: Record<string, any>;
  language_considerations?: Record<string, any>;
}

export interface AnalysisResult {
  taskId: string;
  status: "processing" | "completed" | "failed";
  progress: number;
  thoughts: ThoughtMessage[];
  results?: AnalysisResults;
  error?: string;
}

// Component prop types
export interface AnalysisSectionProps {
  analysisResult: AnalysisResult | null;
  isPolling: boolean;
  onDownloadPDF: () => void;
  type?: 'watson' | 'gemini';
}