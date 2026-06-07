import { usePropertyScope } from '@/context/PropertyScopeContext'
import { Link } from 'react-router-dom'

export function RequirePropertyScope({ children }: { children: React.ReactNode }) {
  const { needsPropertySelection } = usePropertyScope()
  if (needsPropertySelection) {
    return (
      <div className="card text-center py-12 max-w-lg mx-auto">
        <p className="text-gray-700 mb-2">Select a property in the sidebar under <strong>Business Management</strong>.</p>
        <Link to="/admin/platform-dashboard" className="text-blue-600 text-sm hover:underline">Platform Dashboard →</Link>
      </div>
    )
  }
  return <>{children}</>
}
