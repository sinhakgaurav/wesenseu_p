import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useSelector } from 'react-redux'
import type { RootState } from '@/store'
import api from '@/lib/api'
import { isSuperAdmin } from '@/lib/rbac'

const STORAGE_KEY = 'monitour_selected_property_id'

type PropertyOption = { id: string; name: string; city?: string }

type PropertyScopeContextValue = {
  selectedPropertyId: string | null
  setSelectedPropertyId: (id: string | null) => void
  properties: PropertyOption[]
  selectedProperty: PropertyOption | null
  effectivePropertyId: string | null
  needsPropertySelection: boolean
  isLoadingProperties: boolean
}

const PropertyScopeContext = createContext<PropertyScopeContextValue | null>(null)

export function PropertyScopeProvider({ children }: { children: React.ReactNode }) {
  const user = useSelector((state: RootState) => state.auth.user)
  const superAdmin = isSuperAdmin(user?.role)

  const [selectedPropertyId, setSelectedPropertyIdState] = useState<string | null>(() => {
    if (typeof window === 'undefined') return null
    return localStorage.getItem(STORAGE_KEY) || user?.property_id || null
  })

  const setSelectedPropertyId = useCallback((id: string | null) => {
    setSelectedPropertyIdState(id)
    if (id) localStorage.setItem(STORAGE_KEY, id)
    else localStorage.removeItem(STORAGE_KEY)
  }, [])

  useEffect(() => {
    if (!superAdmin && user?.property_id) {
      setSelectedPropertyIdState(user.property_id)
    }
  }, [superAdmin, user?.property_id])

  const { data: properties = [], isLoading: isLoadingProperties } = useQuery<PropertyOption[]>({
    queryKey: ['scope-properties'],
    queryFn: async () => {
      const { data } = await api.get('/properties')
      return (data as { id: string; name: string; city?: string }[]).map((p) => ({
        id: p.id,
        name: p.name,
        city: p.city,
      }))
    },
    enabled: !!user && superAdmin,
  })

  useEffect(() => {
    if (!superAdmin || !properties.length) return
    if (selectedPropertyId && properties.some((p) => p.id === selectedPropertyId)) return
    const fallback = properties[0]?.id
    if (fallback) setSelectedPropertyId(fallback)
  }, [superAdmin, properties, selectedPropertyId, setSelectedPropertyId])

  const effectivePropertyId = superAdmin
    ? selectedPropertyId || user?.property_id || null
    : user?.property_id || null

  const selectedProperty = properties.find((p) => p.id === effectivePropertyId) || null

  const value = useMemo(
    () => ({
      selectedPropertyId,
      setSelectedPropertyId,
      properties,
      selectedProperty,
      effectivePropertyId,
      needsPropertySelection: superAdmin && !effectivePropertyId,
      isLoadingProperties,
    }),
    [
      selectedPropertyId,
      setSelectedPropertyId,
      properties,
      selectedProperty,
      effectivePropertyId,
      superAdmin,
      isLoadingProperties,
    ],
  )

  return <PropertyScopeContext.Provider value={value}>{children}</PropertyScopeContext.Provider>
}

export function usePropertyScope() {
  const ctx = useContext(PropertyScopeContext)
  if (!ctx) {
    throw new Error('usePropertyScope must be used within PropertyScopeProvider')
  }
  return ctx
}
