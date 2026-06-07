import { Fragment, useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Database, ChevronDown, ChevronRight, RefreshCw, Search } from 'lucide-react'
import api from '@/lib/api'

type DbColumn = {
  name: string
  type: string
  nullable: boolean
}

type DbTable = {
  table_name: string
  row_count: number
  columns: DbColumn[]
  has_soft_delete: boolean
}

type DbTablesResponse = {
  schema_name: string
  table_count: number
  tables: DbTable[]
}

export function SuperAdminSchemaTab() {
  const [search, setSearch] = useState('')
  const [expanded, setExpanded] = useState<string | null>(null)

  const { data, isLoading, isFetching, refetch, error } = useQuery<DbTablesResponse>({
    queryKey: ['system-db-tables'],
    queryFn: () => api.get('/system/db-tables').then((r) => r.data),
  })

  const filtered = useMemo(() => {
    const tables = data?.tables ?? []
    const q = search.trim().toLowerCase()
    if (!q) return tables
    return tables.filter(
      (t) =>
        t.table_name.toLowerCase().includes(q) ||
        t.columns.some((c) => c.name.toLowerCase().includes(q) || c.type.toLowerCase().includes(q)),
    )
  }, [data?.tables, search])

  const toggle = (name: string) => {
    setExpanded((prev) => (prev === name ? null : name))
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <Database className="w-5 h-5 text-blue-600" />
            Table schema
          </h2>
          <p className="text-sm text-gray-500 mt-1">
            Live introspection of{' '}
            <code className="bg-gray-100 px-1 rounded text-xs">{data?.schema_name ?? '…'}</code>
            {data != null && (
              <>
                {' '}
                · {data.table_count} table{data.table_count === 1 ? '' : 's'}
              </>
            )}
          </p>
        </div>
        <button
          type="button"
          className="btn-secondary flex items-center gap-2 text-sm"
          disabled={isFetching}
          onClick={() => refetch()}
        >
          <RefreshCw className={`w-4 h-4 ${isFetching ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      <div className="relative max-w-md">
        <Search className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
        <input
          type="search"
          placeholder="Search tables or columns…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="input-field pl-9 w-full"
        />
      </div>

      {error && (
        <div className="card border-red-100 bg-red-50 text-red-700 text-sm">
          Failed to load schema. Super admin access required.
        </div>
      )}

      {isLoading && (
        <div className="card text-center py-12 text-gray-500 text-sm">Loading schema…</div>
      )}

      {!isLoading && !error && filtered.length === 0 && (
        <div className="card text-center py-12 text-gray-500 text-sm">No tables match your search.</div>
      )}

      {!isLoading && filtered.length > 0 && (
        <div className="card p-0 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-gray-500 border-b bg-gray-50">
                  <th className="py-3 px-4 w-8" />
                  <th className="py-3 px-2 font-medium">Table</th>
                  <th className="py-3 px-2 font-medium">Rows</th>
                  <th className="py-3 px-2 font-medium">Columns</th>
                  <th className="py-3 px-2 font-medium">Soft delete</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((table) => {
                  const open = expanded === table.table_name
                  return (
                    <Fragment key={table.table_name}>
                      <tr
                        className="border-b border-gray-50 hover:bg-gray-50/80 cursor-pointer"
                        onClick={() => toggle(table.table_name)}
                      >
                        <td className="py-3 px-4 text-gray-400">
                          {open ? (
                            <ChevronDown className="w-4 h-4" />
                          ) : (
                            <ChevronRight className="w-4 h-4" />
                          )}
                        </td>
                        <td className="py-3 px-2 font-mono text-xs font-medium text-gray-900">
                          {table.table_name}
                        </td>
                        <td className="py-3 px-2 text-gray-600">
                          {table.row_count < 0 ? '—' : table.row_count.toLocaleString()}
                        </td>
                        <td className="py-3 px-2 text-gray-600">{table.columns.length}</td>
                        <td className="py-3 px-2">
                          {table.has_soft_delete ? (
                            <span className="text-xs text-green-700 bg-green-50 px-2 py-0.5 rounded-full">
                              is_active + deleted_at
                            </span>
                          ) : (
                            <span className="text-xs text-gray-400">—</span>
                          )}
                        </td>
                      </tr>
                      {open && (
                        <tr className="bg-gray-50/50">
                          <td colSpan={5} className="px-4 pb-4 pt-0">
                            <div className="ml-8 mt-1 rounded-lg border border-gray-100 bg-white overflow-hidden">
                              <table className="w-full text-xs">
                                <thead>
                                  <tr className="text-gray-500 border-b">
                                    <th className="py-2 px-3 text-left font-medium">Column</th>
                                    <th className="py-2 px-3 text-left font-medium">Type</th>
                                    <th className="py-2 px-3 text-left font-medium">Nullable</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {table.columns.map((col) => (
                                    <tr key={col.name} className="border-b border-gray-50 last:border-0">
                                      <td className="py-2 px-3 font-mono text-gray-900">{col.name}</td>
                                      <td className="py-2 px-3 text-gray-600">{col.type}</td>
                                      <td className="py-2 px-3">
                                        {col.nullable ? (
                                          <span className="text-amber-700">YES</span>
                                        ) : (
                                          <span className="text-gray-700">NO</span>
                                        )}
                                      </td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          </td>
                        </tr>
                      )}
                    </Fragment>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
