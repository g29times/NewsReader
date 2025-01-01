import { Checkbox } from "@/components/ui/checkbox"
import { Button } from "@/components/ui/button"
import { MoreHorizontal, Plus, FileText } from 'lucide-react'

interface SourcesProps {
  isCollapsed: boolean
}

export function Sources({ isCollapsed }: SourcesProps) {
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
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold">Sources</h2>
        <Button size="sm" variant="outline">
          <Plus className="mr-2 h-4 w-4" />
          Add source
        </Button>
      </div>
      <div className="space-y-4">
        <div className="flex items-center space-x-2">
          <Button variant="ghost" size="icon">
            <MoreHorizontal className="h-4 w-4" />
          </Button>
          <div className="flex-1">2001: A Space Odyssey Timeline</div>
          <Checkbox />
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="ghost" size="icon">
            <MoreHorizontal className="h-4 w-4" />
          </Button>
          <div className="flex-1">Arthur C. Clarke - 2001.pdf</div>
          <Checkbox />
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="ghost" size="icon">
            <MoreHorizontal className="h-4 w-4" />
          </Button>
          <div className="flex-1">Arthur C. Clarke - 2010.pdf</div>
          <Checkbox />
        </div>
      </div>
    </div>
  )
}

