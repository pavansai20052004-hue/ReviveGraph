import type { HTMLAttributes, ReactNode } from 'react'
import { cn } from '@/lib/utils'

export function Panel({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <section className={cn('panel', className)} {...props} />
}
export function Badge({ children, tone = 'neutral' }: { children: ReactNode; tone?: string }) {
  return <span className={cn('badge', `badge-${tone}`)}>{children}</span>
}
export function HealthBadge({ value }: { value: string }) {
  return <Badge tone={value === 'healthy' || value === 'compatible' || value === 'usable' ? 'success' : value === 'faulty' || value === 'incompatible' || value === 'unusable' ? 'error' : 'warning'}>{value}</Badge>
}
export function EmptyState({ title, children }: { title: string; children: ReactNode }) {
  return <Panel className="empty-state"><span className="eyebrow">FLEET WORKSPACE</span><h2>{title}</h2><div className="muted">{children}</div></Panel>
}
export function ErrorNotice({ message, children }: { message: string; children?: ReactNode }) {
  return <div className="error-notice" role="alert"><strong>Action needed</strong><p>{message}</p>{children}</div>
}
export function Loading({ text = 'Loading inventory from the backend…' }: { text?: string }) {
  return <div className="loading" role="status"><span className="loading-dot" />{text}</div>
}
