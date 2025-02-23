'use client';
import React, { useState, useEffect } from 'react';
import Image from 'next/image';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { IBM_Plex_Sans } from 'next/font/google';

const ibmPlexSans = IBM_Plex_Sans({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
  variable: '--font-ibm-plex',
});

interface Slide {
  title: string;
  subtitle?: string;
  content: string | string[];
  type: 'title' | 'bullets' | 'technical' | 'pipeline' | 'feature' | 'dashboard' | 'code' | 'features' | 'demo' | 'final';
}

const slides: Slide[] = [
  {
    title: "ProcessLens",
    subtitle: "Process Mining with IBM Granite",
    content: "Enterprise Process Analysis Platform",
    type: "title"
  },
  {
    title: "Problem Statement",
    content: [
      "Manual process analysis is time-consuming",
      "Lack of real-time insights",
      "Difficulty in pattern recognition",
      "Complex data interpretation"
    ],
    type: "bullets"
  },
  {
    title: "Solution Architecture",
    content: [
      "IBM Granite 3.8B Integration",
      "FastAPI Backend",
      "MongoDB Database",
      "Real-time WebSocket Updates"
    ],
    type: "technical"
  },
  {
    title: "Data Processing Pipeline",
    content: [
      "Automatic CSV/Excel Processing",
      "Parallel Analysis Streams",
      "Pattern Detection Engine",
      "Real-time Metric Calculation"
    ],
    type: "pipeline"
  },
  {
    title: "Real-time Analysis",
    content: [
      "Live Thought Process Display",
      "Progress Tracking",
      "Interactive Visualizations",
      "Dynamic Updates"
    ],
    type: "feature"
  },
  {
    title: "Interactive Dashboards",
    content: [
      "Performance Metrics",
      "Resource Utilization",
      "Process Patterns",
      "Bottleneck Detection"
    ],
    type: "dashboard"
  },
  {
    title: "Technical Implementation",
    content: [
      "Next.js 15 & React 19",
      "FastAPI with MongoDB",
      "WebSocket Integration",
      "Comprehensive Error Handling"
    ],
    type: "code"
  },
  {
    title: "Features Overview",
    content: [
      "Robust Data Validation",
      "PDF Report Generation",
      "Dark/Light Theme Support",
      "Enterprise-grade Security"
    ],
    type: "features"
  },
  {
    title: "Live Demo Setup",
    content: [
      "Sample Dataset Ready",
      "Environment Configured",
      "Test Cases Prepared",
      "Real-time Monitoring"
    ],
    type: "demo"
  },
  {
    title: "Next Steps",
    content: [
      "Documentation Access",
      "Deployment Guide",
      "API Reference",
      "Support Channels"
    ],
    type: "final"
  }
];

const SlidesPage = () => {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [isAutoPlaying, setIsAutoPlaying] = useState(false);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isAutoPlaying) {
      interval = setInterval(() => {
        setCurrentSlide((prev) => (prev === slides.length - 1 ? 0 : prev + 1));
      }, 5000);
    }
    return () => clearInterval(interval);
  }, [isAutoPlaying]);

  const nextSlide = () => {
    setCurrentSlide((prev) => (prev === slides.length - 1 ? 0 : prev + 1));
  };

  const prevSlide = () => {
    setCurrentSlide((prev) => (prev === 0 ? slides.length - 1 : prev - 1));
  };

  return (
    <div className={`min-h-screen bg-background text-foreground ${ibmPlexSans.variable}`}>
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8 flex items-center justify-between">
          <div className="relative h-12 w-48">
            <Image
              src="/logo.png"
              alt="ProcessLens Logo"
              fill
              className="object-contain"
              priority
            />
          </div>
          <Button
            variant="outline"
            onClick={() => setIsAutoPlaying(!isAutoPlaying)}
          >
            {isAutoPlaying ? 'Pause' : 'Auto Play'}
          </Button>
        </div>

        <div className="relative h-[600px] w-full overflow-hidden rounded-lg border bg-card">
          <AnimatePresence mode="wait">
            <motion.div
              key={currentSlide}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.5 }}
              className="h-full w-full p-12"
            >
              <Card className="h-full bg-opacity-50 backdrop-blur">
                <CardContent className="flex h-full flex-col items-center justify-center p-8">
                  <h2 className="mb-8 text-4xl font-bold tracking-tight">
                    {slides[currentSlide].title}
                  </h2>
                  
                  {slides[currentSlide].type === "title" ? (
                    <div className="text-center">
                      <p className="mb-4 text-2xl text-muted-foreground">
                        {slides[currentSlide].subtitle}
                      </p>
                      <p className="text-xl">{slides[currentSlide].content}</p>
                    </div>
                  ) : (
                    <ul className="space-y-4 text-xl">
                      {Array.isArray(slides[currentSlide].content) && 
                        slides[currentSlide].content.map((item, index) => (
                          <motion.li
                            key={index}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: index * 0.1 }}
                            className="flex items-center"
                          >
                            <span className="mr-2 h-2 w-2 rounded-full bg-primary" />
                            {item}
                          </motion.li>
                        ))}
                    </ul>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          </AnimatePresence>

          <div className="absolute bottom-4 left-0 right-0 flex justify-center space-x-2">
            {slides.map((_, index) => (
              <button
                key={index}
                onClick={() => setCurrentSlide(index)}
                className={`h-2 w-2 rounded-full transition-all ${
                  currentSlide === index ? 'bg-primary w-4' : 'bg-muted'
                }`}
              />
            ))}
          </div>

          <Button
            variant="ghost"
            className="absolute left-4 top-1/2 -translate-y-1/2"
            onClick={prevSlide}
          >
            <ChevronLeft className="h-8 w-8" />
          </Button>

          <Button
            variant="ghost"
            className="absolute right-4 top-1/2 -translate-y-1/2"
            onClick={nextSlide}
          >
            <ChevronRight className="h-8 w-8" />
          </Button>
        </div>
      </div>
    </div>
  );
};

export default SlidesPage;