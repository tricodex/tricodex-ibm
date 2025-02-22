export interface ThoughtMessage {
  timestamp: string;
  stage?: string;
  thought: string;
  progress: number;
}

export interface Improvement {
  action: string;
  expected_impact: number;
  implementation_complexity: number;
  suggestion: string;
}

export interface AnalysisResults {
  performance?: any;
  patterns?: any[];
  improvements?: Improvement[];
  insights?: string[];
  bottlenecks?: string[];
  recommendations?: string[];
  data_quality_impact?: Record<string, any>;
  language_considerations?: Record<string, any>;
}

export interface AnalysisResult {
  status: "processing" | "completed" | "failed";
  progress: number;
  thoughts: ThoughtMessage[];
  results?: AnalysisResults;
  error?: string;
}
