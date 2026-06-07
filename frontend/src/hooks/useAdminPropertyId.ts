import { usePropertyScope } from '@/context/PropertyScopeContext'

/** Resolved property id for admin API calls (super_admin uses sidebar selection). */
export function useAdminPropertyId() {
  const { effectivePropertyId, needsPropertySelection, selectedProperty } = usePropertyScope()
  const propertyId = effectivePropertyId || ''

  return {
    propertyId,
    enabled: !!propertyId,
    needsPropertySelection,
    selectedProperty,
    querySuffix: propertyId ? `property_id=${propertyId}` : '',
    withPropertyParams: (params: URLSearchParams) => {
      if (propertyId) params.set('property_id', propertyId)
      return params
    },
  }
}
