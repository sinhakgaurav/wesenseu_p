import clsx from 'clsx'
import type { LucideIcon } from 'lucide-react'

interface StatCardProps {
  title: string
  value: number | string
  icon: LucideIcon
  iconBg?: string
  iconColor?: string
  subtitle?: string
  trend?: number
  onClick?: () => void
}

export function StatCard({
  title,
  value,
  icon: Icon,
  iconBg = 'bg-blue-50',
  iconColor = 'text-blue-600',
  subtitle,
  onClick,
}: StatCardProps) {
  return (
    <div
      className={clsx(
        'bg-white rounded-xl p-5 shadow-sm border border-gray-100 flex items-start gap-4',
        onClick && 'cursor-pointer hover:shadow-md transition-shadow'
      )}
      onClick={onClick}
    >
      <div className={clsx('p-3 rounded-xl flex-shrink-0', iconBg)}>
        <Icon className={clsx('w-5 h-5', iconColor)} />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-gray-500 font-medium">{title}</p>
        <p className="text-2xl font-bold text-gray-900 mt-0.5">{value}</p>
        {subtitle && <p className="text-xs text-gray-400 mt-1">{subtitle}</p>}
      </div>
    </div>
  )
}
