import { Button } from "@/components/ui/button"
import { Plus, FileText, Book, MessageSquare, TimerIcon as Timeline, Play } from 'lucide-react'

interface NotesProps {
  isCollapsed: boolean
}

export function Notes({ isCollapsed }: NotesProps) {
  if (isCollapsed) {
    return (
      <div className="p-2">
        <Button variant="ghost" size="icon" className="w-full">
          <FileText className="h-4 w-4" />
        </Button>
      </div>
    )
  }

  return (
    <div className="h-full p-4">
      <div className="mb-6 space-y-4">
        <div className="rounded-lg border p-4">
          <h3 className="mb-2 font-medium">Audio Overview</h3>
          <Button variant="outline" className="w-full">
            <Play className="mr-2 h-4 w-4" />
            Play Audio
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <Button variant="outline" className="flex flex-col gap-2 h-auto p-4">
          <Plus className="h-4 w-4" />
          <span>Add note</span>
        </Button>
        <Button variant="outline" className="flex flex-col gap-2 h-auto p-4">
          <Book className="h-4 w-4" />
          <span>Study guide</span>
        </Button>
        <Button variant="outline" className="flex flex-col gap-2 h-auto p-4">
          <FileText className="h-4 w-4" />
          <span>Briefing doc</span>
        </Button>
        <Button variant="outline" className="flex flex-col gap-2 h-auto p-4">
          <MessageSquare className="h-4 w-4" />
          <span>FAQ</span>
        </Button>
        <Button variant="outline" className="col-span-2 flex flex-col gap-2 h-auto p-4">
          <Timeline className="h-4 w-4" />
          <span>Timeline</span>
        </Button>
      </div>

      <div className="mt-6">
        <h3 className="mb-4 font-medium">Saved Notes</h3>
        <div className="space-y-2">
          <div className="rounded-lg border p-3">
            <h4 className="font-medium">Clarke's Space Odyssey: Overview</h4>
            <p className="text-sm text-muted-foreground">
              These texts are excerpts from Arthur C. Clarke's Space Odyssey series...
            </p>
          </div>
          <div className="rounded-lg border p-3">
            <h4 className="font-medium">Space Odyssey: Q&A</h4>
            <p className="text-sm text-muted-foreground">
              Frequently Asked Questions: Arthur C. Clarke's Space Odyssey...
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

