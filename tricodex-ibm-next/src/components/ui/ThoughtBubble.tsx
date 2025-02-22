import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { cn } from '@/lib/utils'

interface ThoughtBubbleProps {
  thought: string
  timestamp: string
  type: 'watson' | 'gemini'
  isActive?: boolean
}

export const ThoughtBubble = ({
  thought,
  timestamp,
  type,
  isActive = false
}: ThoughtBubbleProps) => {
  const [displayedText, setDisplayedText] = useState('')
  
  useEffect(() => {
    let index = 0
    const timer = setInterval(() => {
      if (index <= thought.length) {
        setDisplayedText(thought.slice(0, index))
        index++
      } else {
        clearInterval(timer)
      }
    }, 30) // Adjust speed as needed
    
    return () => clearInterval(timer)
  }, [thought])

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className={cn(
        "rounded-lg p-4 mb-2 max-w-[80%]",
        type === 'watson' ? "bg-blue-50 ml-auto" : "bg-emerald-50",
        isActive && "border-2 border-primary"
      )}
    >
      <div className="text-sm mb-1 opacity-50">{timestamp}</div>
      <div className={cn(
        "font-mono",
        type === 'watson' ? "text-blue-800" : "text-emerald-800"
      )}>
        {displayedText}
        {displayedText.length < thought.length && (
          <span className="animate-pulse">▋</span>
        )}
      </div>
    </motion.div>
  )
}
