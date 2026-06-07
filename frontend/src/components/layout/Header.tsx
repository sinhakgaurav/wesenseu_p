import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Bell, Menu } from 'lucide-react'
import { useSelector } from 'react-redux'
import type { RootState } from '@/store'
import api from '@/lib/api'

interface HeaderProps {
  onMenuToggle: () => void
  title?: string
}

type Notification = {
  id: string
  title: string
  message: string
  is_read: boolean
}

export function Header({ onMenuToggle, title }: HeaderProps) {
  const user = useSelector((state: RootState) => state.auth.user)
  const queryClient = useQueryClient()
  const [open, setOpen] = useState(false)

  const { data: notifications = [] } = useQuery<Notification[]>({
    queryKey: ['notifications', user?.id],
    enabled: !!user?.id,
    queryFn: async () => {
      const { data } = await api.get('/notifications?unread_only=true&limit=20')
      return data
    },
    refetchInterval: 30000,
  })

  const markAllRead = useMutation({
    mutationFn: () => api.post('/notifications/read-all'),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['notifications'] }),
  })

  const unread = notifications.filter((n) => !n.is_read).length

  return (
    <header className="bg-white border-b border-gray-100 px-6 py-4 flex items-center gap-4">
      <button
        onClick={onMenuToggle}
        className="p-2 rounded-lg hover:bg-gray-100 transition-colors lg:hidden"
        type="button"
      >
        <Menu className="w-5 h-5 text-gray-600" />
      </button>

      {title && <h1 className="text-lg font-semibold text-gray-900 hidden lg:block">{title}</h1>}

      <div className="flex-1" />

      <div className="relative">
        <button
          type="button"
          onClick={() => setOpen(!open)}
          className="relative p-2 rounded-lg hover:bg-gray-100 transition-colors"
        >
          <Bell className="w-5 h-5 text-gray-600" />
          {unread > 0 && (
            <span className="absolute top-1 right-1 min-w-[18px] h-[18px] px-1 bg-red-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center">
              {unread > 9 ? '9+' : unread}
            </span>
          )}
        </button>
        {open && (
          <div className="absolute right-0 mt-2 w-80 bg-white border border-gray-100 rounded-xl shadow-lg z-50 max-h-96 overflow-y-auto">
            <div className="p-3 border-b flex justify-between items-center">
              <span className="font-medium text-sm">Notifications</span>
              {unread > 0 && (
                <button type="button" className="text-xs text-blue-600" onClick={() => markAllRead.mutate()}>
                  Mark all read
                </button>
              )}
            </div>
            {notifications.length === 0 ? (
              <p className="p-4 text-sm text-gray-500">No new notifications</p>
            ) : (
              notifications.map((n) => (
                <div key={n.id} className={`p-3 border-b text-sm ${n.is_read ? 'opacity-60' : ''}`}>
                  <p className="font-medium text-gray-900">{n.title}</p>
                  <p className="text-gray-500 text-xs mt-0.5">{n.message}</p>
                </div>
              ))
            )}
          </div>
        )}
      </div>

      <div className="flex items-center gap-2">
        <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white text-sm font-semibold">
          {user?.full_name[0].toUpperCase()}
        </div>
        <div className="hidden md:block">
          <p className="text-sm font-medium text-gray-900">{user?.full_name}</p>
          <p className="text-xs text-gray-500 capitalize">{user?.role?.replace('_', ' ')}</p>
        </div>
      </div>
    </header>
  )
}
