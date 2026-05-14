import clsx from 'clsx'

const variantMap: Record<string, string> = {
  green: 'bg-green-100 text-green-800',
  red: 'bg-red-100 text-red-800',
  yellow: 'bg-yellow-100 text-yellow-800',
  blue: 'bg-blue-100 text-blue-800',
  purple: 'bg-purple-100 text-purple-800',
  gray: 'bg-gray-100 text-gray-700',
  orange: 'bg-orange-100 text-orange-800',
  indigo: 'bg-indigo-100 text-indigo-800',
}

const priorityMap: Record<string, string> = {
  low: 'green',
  medium: 'yellow',
  high: 'orange',
  critical: 'red',
}

const statusColorMap: Record<string, string> = {
  pending: 'gray',
  assigned: 'blue',
  in_progress: 'yellow',
  verification_pending: 'purple',
  approved: 'green',
  completed: 'green',
  rejected: 'red',
  rework_required: 'orange',
  cancelled: 'gray',
  open: 'blue',
  resolved: 'green',
  closed: 'gray',
  escalated: 'red',
  occupied: 'blue',
  vacant: 'green',
  cleaning_pending: 'yellow',
  cleaning_in_progress: 'orange',
  ready: 'green',
  maintenance: 'red',
  inspection_pending: 'purple',
  blocked: 'gray',
  active: 'green',
  inactive: 'gray',
  suspended: 'red',
}

interface BadgeProps {
  children: React.ReactNode
  variant?: string
  priority?: string
  status?: string
  className?: string
}

export function Badge({ children, variant, priority, status, className }: BadgeProps) {
  const color = variant ?? (priority ? priorityMap[priority] : status ? statusColorMap[status] : 'gray')
  return (
    <span
      className={clsx(
        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
        variantMap[color] || variantMap.gray,
        className
      )}
    >
      {children}
    </span>
  )
}

export function PriorityBadge({ priority }: { priority: string }) {
  return <Badge priority={priority}>{priority.charAt(0).toUpperCase() + priority.slice(1)}</Badge>
}

export function StatusBadge({ status }: { status: string }) {
  return (
    <Badge status={status}>
      {status.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
    </Badge>
  )
}
