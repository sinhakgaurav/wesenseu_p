import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Activity, RefreshCw, CheckCircle, AlertTriangle, XCircle,
  Server, Cpu, Layers,
} from 'lucide-react'
import api from '@/lib/api'

type Check = {
  id: string
  name: string
  category: string
  status: 'ok' | 'warn' | 'error' | 'skip'
  latency_ms: number
  message: string
  detail?: Record<string, unknown>
}

type DiagnosticsResult = {
  summary: { total: number; ok: number; warn: number; error: number }
  property_id_used?: string
  checks: Check[]
}

const STATUS_ICON = {
  ok: CheckCircle,
  warn: AlertTriangle,
  error: XCircle,
  skip: AlertTriangle,
}

const STATUS_CLASS = {
  ok: 'text-green-600 bg-green-50 border-green-100',
  warn: 'text-amber-700 bg-amber-50 border-amber-100',
  error: 'text-red-600 bg-red-50 border-red-100',
  skip: 'text-gray-500 bg-gray-50 border-gray-100',
}

const CAT_ICON: Record<string, typeof Server> = {
  infrastructure: Server,
  microservice: Cpu,
  module: Layers,
}

export function SuperAdminDiagnosticsTab() {
  const qc = useQueryClient()
  const [filter, setFilter] = useState<'all' | 'error' | 'warn' | 'ok'>('all')
  const [expanded, setExpanded] = useState<string | null>(null)

  const { data: catalog } = useQuery({
    queryKey: ['diagnostics-modules'],
    queryFn: () => api.get('/system/diagnostics/modules').then((r) => r.data),
  })

  const runAll = useMutation({
    mutationFn: () => api.get('/system/diagnostics/run').then((r) => r.data as DiagnosticsResult),
    onSuccess: (data) => {
      qc.setQueryData(['diagnostics-run'], data)
    },
  })

  const { data: lastRun } = useQuery<DiagnosticsResult>({
    queryKey: ['diagnostics-run'],
    enabled: false,
    queryFn: () => api.get('/system/diagnostics/run').then((r) => r.data),
  })

  const result = runAll.data ?? lastRun

  const rerunOne = useMutation({
    mutationFn: (moduleId: string) =>
      api.post(`/system/diagnostics/run/${moduleId}`).then((r) => r.data.check as Check),
    onSuccess: (check) => {
      qc.setQueryData<DiagnosticsResult>(['diagnostics-run'], (old) => {
        if (!old) return old
        const checks = old.checks.map((c) => (c.id === check.id ? check : c))
        const summary = {
          total: checks.length,
          ok: checks.filter((c) => c.status === 'ok').length,
          warn: checks.filter((c) => c.status === 'warn').length,
          error: checks.filter((c) => c.status === 'error').length,
        }
        return { ...old, summary, checks }
      })
    },
  })

  const checks = (result?.checks ?? []).filter((c) => filter === 'all' || c.status === filter)
  const grouped = {
    infrastructure: checks.filter((c) => c.category === 'infrastructure'),
    microservice: checks.filter((c) => c.category === 'microservice'),
    module: checks.filter((c) => c.category === 'module'),
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <Activity className="w-5 h-5 text-blue-600" />
            System diagnostics
          </h2>
          <p className="text-sm text-gray-500 mt-1">
            Test PostgreSQL, Redis, WesenseU, Celery, and each API module in one place.
          </p>
        </div>
        <button
          type="button"
          className="btn-primary flex items-center gap-2"
          disabled={runAll.isPending}
          onClick={() => runAll.mutate()}
        >
          <RefreshCw className={`w-4 h-4 ${runAll.isPending ? 'animate-spin' : ''}`} />
          {runAll.isPending ? 'Running…' : 'Run all checks'}
        </button>
      </div>

      {result && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { label: 'Total', value: result.summary.total, cls: 'bg-gray-50' },
            { label: 'OK', value: result.summary.ok, cls: 'bg-green-50 text-green-800' },
            { label: 'Warnings', value: result.summary.warn, cls: 'bg-amber-50 text-amber-800' },
            { label: 'Errors', value: result.summary.error, cls: 'bg-red-50 text-red-800' },
          ].map(({ label, value, cls }) => (
            <div key={label} className={`card text-center py-4 ${cls}`}>
              <p className="text-2xl font-bold">{value}</p>
              <p className="text-xs font-medium uppercase tracking-wide opacity-80">{label}</p>
            </div>
          ))}
        </div>
      )}

      {result?.property_id_used && (
        <p className="text-xs text-gray-500">
          Property-scoped probes used property <code className="bg-gray-100 px-1 rounded">{result.property_id_used}</code>
        </p>
      )}

      <div className="flex gap-2 flex-wrap">
        {(['all', 'ok', 'warn', 'error'] as const).map((f) => (
          <button
            key={f}
            type="button"
            onClick={() => setFilter(f)}
            className={`px-3 py-1 rounded-lg text-sm font-medium ${
              filter === f ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {f === 'all' ? 'All' : f}
          </button>
        ))}
      </div>

      {!result && !runAll.isPending && (
        <div className="card text-center py-12 text-gray-500">
          <Activity className="w-12 h-12 mx-auto mb-3 opacity-40" />
          <p>Click &quot;Run all checks&quot; to probe the stack.</p>
          {catalog?.modules && (
            <p className="text-xs mt-2">{catalog.modules.length} targets available</p>
          )}
        </div>
      )}

      {(['infrastructure', 'microservice', 'module'] as const).map((cat) => {
        const items = grouped[cat]
        if (!items.length) return null
        const CatIcon = CAT_ICON[cat] ?? Layers
        return (
          <section key={cat}>
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-3 flex items-center gap-2">
              <CatIcon className="w-4 h-4" />
              {cat}
            </h3>
            <div className="space-y-2">
              {items.map((check) => {
                const Icon = STATUS_ICON[check.status] ?? AlertTriangle
                const open = expanded === check.id
                return (
                  <div
                    key={check.id}
                    className={`border rounded-xl p-4 ${STATUS_CLASS[check.status]}`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-start gap-3 min-w-0">
                        <Icon className="w-5 h-5 flex-shrink-0 mt-0.5" />
                        <div className="min-w-0">
                          <p className="font-semibold text-gray-900">{check.name}</p>
                          <p className="text-sm opacity-90">{check.message}</p>
                          <p className="text-xs mt-1 opacity-70">{check.latency_ms} ms</p>
                        </div>
                      </div>
                      <div className="flex gap-2 flex-shrink-0">
                        <button
                          type="button"
                          className="text-xs btn-secondary py-1 px-2"
                          onClick={() => setExpanded(open ? null : check.id)}
                        >
                          {open ? 'Hide' : 'Detail'}
                        </button>
                        <button
                          type="button"
                          className="text-xs btn-secondary py-1 px-2"
                          disabled={rerunOne.isPending}
                          onClick={() => rerunOne.mutate(check.id)}
                        >
                          Retry
                        </button>
                      </div>
                    </div>
                    {open && check.detail && (
                      <pre className="mt-3 text-xs bg-white/60 rounded-lg p-3 overflow-auto max-h-40">
                        {JSON.stringify(check.detail, null, 2)}
                      </pre>
                    )}
                  </div>
                )
              })}
            </div>
          </section>
        )
      })}
    </div>
  )
}
