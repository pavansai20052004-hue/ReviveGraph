import {
  Activity, AlertTriangle, ArrowDownToLine, ArrowRight, Bell, Boxes,
  CheckCircle2, ChevronDown, ChevronLeft, CircleHelp, ClipboardCheck,
  FileBarChart2, GitBranch, LayoutDashboard, ListChecks, MemoryStick,
  Menu, Monitor, Network, Play, RefreshCw, Search, ShieldCheck, Sparkles,
  Workflow, X,
} from 'lucide-react'

const icons = {
  activity: Activity, alert: AlertTriangle, arrow: ArrowRight, bell: Bell,
  boxes: Boxes, check: CheckCircle2, chevron: ChevronDown, collapse: ChevronLeft,
  clipboard: ClipboardCheck, compatibility: Network, dashboard: LayoutDashboard,
  download: ArrowDownToLine, help: CircleHelp, inventory: Monitor, list: ListChecks,
  memory: MemoryStick, menu: Menu, optimizer: GitBranch, play: Play,
  refresh: RefreshCw, reports: FileBarChart2, search: Search, shield: ShieldCheck,
  sparkles: Sparkles, workflow: Workflow, close: X,
}
export type IconName = keyof typeof icons
export function Icon({ name, size = 18, className = '' }: { name: IconName; size?: number; className?: string }) {
  const Component = icons[name]
  return <Component size={size} strokeWidth={1.65} aria-hidden="true" className={className} />
}
