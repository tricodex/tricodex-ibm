import React from 'react';
import { Bot, Sparkles, Brain, Cpu, Network } from 'lucide-react';
import { TextGenerateEffect } from '@/components/ui/text-generate-effect';
import { TextShimmer } from '@/components/ui/text-shimmer';
import { cn } from '@/lib/utils';
import { Card, CardContent } from "@/components/ui/card";

interface ThoughtMessage {
  timestamp: string;
  stage: string;
  thought: string;
  progress: number;
}

const StageEmoji = {
  'structure_analysis': {
    icon: Brain,
    color: 'text-blue-500',
    label: 'Structure Analysis'
  },
  'pattern_mining': {
    icon: Network,
    color: 'text-green-500',
    label: 'Pattern Mining'
  },
  'performance_analysis': {
    icon: Cpu,
    color: 'text-purple-500',
    label: 'Performance Analysis'
  },
  'improvement_generation': {
    icon: Sparkles,
    color: 'text-yellow-500',
    label: 'Improvements'
  },
  'final_synthesis': {
    icon: Bot,
    color: 'text-primary',
    label: 'Final Synthesis'
  }
};

const LoadingPulse = () => (
  <div className="flex flex-col items-center justify-center py-12 space-y-8">
    <div className="relative">
      {/* Animated rings */}
      <div className="absolute inset-0 animate-ping-slow rounded-full bg-primary/20" />
      <div className="absolute inset-0 animate-pulse rounded-full bg-primary/10" />
      <div className="relative rounded-full bg-background p-4">
        <Bot className="h-8 w-8 text-primary animate-pulse" />
      </div>
    </div>
    <div className="max-w-sm text-center space-y-4">
      <TextShimmer className="text-lg font-semibold">
        Initializing Process Analysis
      </TextShimmer>
      <div className="flex justify-center space-x-2">
        <span className="animate-bounce delay-0">•</span>
        <span className="animate-bounce delay-150">•</span>
        <span className="animate-bounce delay-300">•</span>
      </div>
    </div>
    <div className="w-full max-w-md space-y-2">
      <div className="h-2 bg-muted rounded-full overflow-hidden">
        <div className="h-full bg-primary/50 w-1/3 animate-progress" />
      </div>
      <div className="flex justify-between text-xs text-muted-foreground">
        <span>Preparing Models</span>
        <span>Analyzing Patterns</span>
        <span>Generating Insights</span>
      </div>
    </div>
  </div>
);

const EmptyState = () => (
  <Card>
    <CardContent className="flex flex-col items-center justify-center py-8 text-center space-y-4">
      <div className="rounded-full bg-primary/10 p-4">
        <Bot className="h-8 w-8 text-primary" />
      </div>
      <div>
        <h3 className="font-semibold">No Analysis In Progress</h3>
        <p className="text-sm text-muted-foreground mt-1">
          Upload a file to begin process analysis
        </p>
      </div>
    </CardContent>
  </Card>
);

export const AnimatedThoughts = ({ 
  thoughts, 
  isProcessing 
}: { 
  thoughts: ThoughtMessage[];
  isProcessing: boolean;
}) => {
  if (isProcessing && thoughts.length === 0) {
    return <LoadingPulse />;
  }

  if (!isProcessing && thoughts.length === 0) {
    return <EmptyState />;
  }

  return (
    <div className="space-y-6">
      {/* Header with icon animation */}
      <div className="flex items-center gap-3">
        <div className="relative">
          <Bot className="h-6 w-6 text-primary relative z-10" />
          {isProcessing && (
            <div className="absolute inset-0 bg-primary/20 rounded-full animate-ping" />
          )}
        </div>
        <TextShimmer as="h2" className="text-xl font-semibold">
          Analysis Thoughts
        </TextShimmer>
      </div>
      
      {/* Thoughts container */}
      <div className="space-y-4 max-h-[400px] overflow-y-auto pr-4">
        {thoughts.map((thought, index) => {
          const StageIcon = StageEmoji[thought.stage as keyof typeof StageEmoji]?.icon || Bot;
          const stageColor = StageEmoji[thought.stage as keyof typeof StageEmoji]?.color || 'text-primary';
          
          return (
            <Card
              key={index}
              className={cn(
                "transition-all duration-500",
                index === thoughts.length - 1 && "border-primary/50 shadow-lg"
              )}
            >
              <CardContent className="p-4 space-y-3">
                {/* Stage badge and timestamp */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className={cn("rounded-full p-1.5 bg-background", stageColor)}>
                      <StageIcon className="h-4 w-4" />
                    </div>
                    <span className="text-sm font-medium">
                      {StageEmoji[thought.stage as keyof typeof StageEmoji]?.label || thought.stage}
                    </span>
                  </div>
                  <span className="text-xs text-muted-foreground">
                    {new Date(thought.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                
                {/* Thought content with animation */}
                <div className="pl-2">
                  <TextGenerateEffect 
                    words={thought.thought}
                    className="text-sm"
                    duration={index === thoughts.length - 1 ? 0.5 : 0}
                  />
                </div>
                
                {/* Progress bar for active thought */}
                {index === thoughts.length - 1 && isProcessing && (
                  <div className="h-1 w-full bg-muted rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-primary animate-pulse rounded-full"
                      style={{ width: `${thought.progress}%` }}
                    />
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
};