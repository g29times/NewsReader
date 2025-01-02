'use client'

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { MessageSquare, ThumbsUp, ThumbsDown, Copy, Pin, Send } from 'lucide-react'
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"

export function Chat() {
  const [messages, setMessages] = useState([
    {
      type: "summary",
      content: "These texts are excerpts from Arthur C. Clarke's Space Odyssey series, detailing events across several decades.",
    },
    {
      type: "ai",
      content: "Here are five characters from the book 2001: A Space Odyssey:\n\n• Dr. Heywood Floyd ①\n• Dr. Chandra ①\n• Frank Poole ②\n• Dimitri ②\n• HAL 9000 ③",
      sources: [
        { id: 1, text: "Source 1: Character descriptions from Chapter 1" },
        { id: 2, text: "Source 2: Mission crew manifest" },
        { id: 3, text: "Source 3: AI systems documentation" },
      ],
    },
  ])

  return (
    <div className="flex h-full flex-col">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message, index) => (
          <div key={index} className="space-y-2">
            {message.type === "summary" ? (
              <div className="rounded-lg bg-muted p-4">{message.content}</div>
            ) : (
              <div className="flex gap-4">
                <Avatar>
                  <AvatarImage src="/placeholder.svg" />
                  <AvatarFallback>AI</AvatarFallback>
                </Avatar>
                <div className="flex-1 space-y-2">
                  <div className="prose prose-sm">{message.content}</div>
                  {message.sources && (
                    <TooltipProvider>
                      <div className="flex gap-2">
                        {message.sources.map((source) => (
                          <Tooltip key={source.id}>
                            <TooltipTrigger asChild>
                              <span className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-primary/10 text-xs text-primary">
                                {source.id}
                              </span>
                            </TooltipTrigger>
                            <TooltipContent>{source.text}</TooltipContent>
                          </Tooltip>
                        ))}
                      </div>
                    </TooltipProvider>
                  )}
                  <div className="flex gap-2">
                    <Button variant="ghost" size="icon">
                      <Pin className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="icon">
                      <Copy className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="icon">
                      <ThumbsUp className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="icon">
                      <ThumbsDown className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Input Area */}
      <div className="border-t p-4">
        <div className="space-y-4">
          <Textarea
            placeholder="Start typing..."
            className="min-h-[100px]"
          />
          <div className="flex items-center justify-between">
            <div className="flex gap-2">
              <Button variant="outline" size="sm">
                Compare characters
              </Button>
              <Button variant="outline" size="sm">
                Analyze themes
              </Button>
              <Button variant="outline" size="sm">
                Discuss plot
              </Button>
            </div>
            <Button>
              <Send className="mr-2 h-4 w-4" />
              Send
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}

