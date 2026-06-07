import { usePropertyScope } from '@/context/PropertyScopeContext'
import { isSuperAdmin } from '@/lib/rbac'
import { useSelector } from 'react-redux'
import type { RootState } from '@/store'
import { Building2 } from 'lucide-react'

export function PropertyScopeBar() {
  const user = useSelector((state: RootState) => state.auth.user)
  const {
    properties,
    selectedPropertyId,
    setSelectedPropertyId,
    selectedProperty,
    effectivePropertyId,
    isLoadingProperties,
  } = usePropertyScope()

  if (!isSuperAdmin(user?.role)) return null

  return (
    <div className="mb-4 flex flex-wrap items-center gap-3 p-3 bg-indigo-50 border border-indigo-100 rounded-xl">
      <Building2 className="w-5 h-5 text-indigo-600 flex-shrink-0" />
      <div className="flex-1 min-w-[200px]">
        <p className="text-xs font-semibold text-indigo-800 uppercase tracking-wide">Business context</p>
        <p className="text-xs text-indigo-600">Select a property for operations below</p>
      </div>
      <select
        className="input-field max-w-xs text-sm"
        value={selectedPropertyId || effectivePropertyId || ''}
        onChange={(e) => setSelectedPropertyId(e.target.value || null)}
        disabled={isLoadingProperties}
      >
        <option value="">— Select property —</option>
        {properties.map((p) => (
          <option key={p.id} value={p.id}>
            {p.name}{p.city ? ` (${p.city})` : ''}
          </option>
        ))}
      </select>
      {selectedProperty && (
        <span className="text-xs text-indigo-700 font-medium">{selectedProperty.name}</span>
      )}
    </div>
  )
}
