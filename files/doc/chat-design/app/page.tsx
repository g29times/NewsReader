'use client'

import { useState } from "react"
import { Sources } from "@/components/sources"
import { Chat } from "@/components/chat"
import { Notes } from "@/components/notes"
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { Button } from "@/components/ui/button"

export default function NotebookPage() {
  const [isSourcesCollapsed, setIsSourcesCollapsed] = useState(false)
  const [isNotesCollapsed, setIsNotesCollapsed] = useState(false)

  return (
    <div className="flex h-screen bg-background">
      {/* Sources Panel */}
      <div
        className={`relative border-r ${
          isSourcesCollapsed ? "w-[50px]" : "w-[300px]"
        } transition-all duration-300 ease-in-out`}
      >
        <Button
          variant="ghost"
          size="icon"
          className="absolute -right-4 top-1/2 z-10 h-8 w-8 rounded-full border bg-background"
          onClick={() => setIsSourcesCollapsed(!isSourcesCollapsed)}
        >
          {isSourcesCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </Button>
        <Sources isCollapsed={isSourcesCollapsed} />
      </div>

      {/* Chat Panel */}
      <div className="flex-1 border-r">
        <Chat />
      </div>

      {/* Notes Panel */}
      <div
        className={`relative ${
          isNotesCollapsed ? "w-[50px]" : "w-[300px]"
        } transition-all duration-300 ease-in-out`}
      >
        <Button
          variant="ghost"
          size="icon"
          className="absolute -left-4 top-1/2 z-10 h-8 w-8 rounded-full border bg-background"
          onClick={() => setIsNotesCollapsed(!isNotesCollapsed)}
        >
          {isNotesCollapsed ? <ChevronLeft className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
        </Button>
        <Notes isCollapsed={isNotesCollapsed} />
      </div>
    </div>
  )
}

