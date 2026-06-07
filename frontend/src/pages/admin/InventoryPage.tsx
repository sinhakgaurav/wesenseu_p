import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Package, AlertTriangle, ArrowUp, ArrowDown, Search, Pencil, Trash2, ImagePlus } from 'lucide-react'
import api from '@/lib/api'
import type { InventoryItem } from '@/lib/types'
import { Modal } from '@/components/ui/Modal'
import { PageLoader } from '@/components/ui/LoadingSpinner'
import toast from 'react-hot-toast'
import { useSelector } from 'react-redux'
import type { RootState } from '@/store'
import { usePropertyScope } from '@/context/PropertyScopeContext'
import { RequirePropertyScope } from '@/components/layout/RequirePropertyScope'

const CATEGORIES = ['Toiletries', 'Cleaning', 'Towels', 'Bedsheets', 'Kitchen', 'Medical', 'Guest Consumables', 'Laundry']

export function InventoryPage() {
  const queryClient = useQueryClient()
  const user = useSelector((state: RootState) => state.auth.user)
  const { effectivePropertyId } = usePropertyScope()
  const propertyId = effectivePropertyId || ''

  const [searchQuery, setSearchQuery] = useState('')
  const [filterCategory, setFilterCategory] = useState('')
  const [showLowStockOnly, setShowLowStockOnly] = useState(false)
  const [showAddModal, setShowAddModal] = useState(false)
  const [showTransactionModal, setShowTransactionModal] = useState(false)
  const [selectedItem, setSelectedItem] = useState<InventoryItem | null>(null)
  const [transactionType, setTransactionType] = useState<'IN' | 'OUT'>('IN')
  const [transactionQty, setTransactionQty] = useState(1)
  const [transactionNotes, setTransactionNotes] = useState('')
  const [showEditModal, setShowEditModal] = useState(false)
  const [editItem, setEditItem] = useState<InventoryItem | null>(null)
  const [editForm, setEditForm] = useState({ item_name: '', minimum_stock: 5, unit_cost: '' })

  const [newItem, setNewItem] = useState({
    item_name: '',
    category: 'Toiletries',
    unit: 'piece',
    current_stock: 0,
    minimum_stock: 5,
    unit_cost: '',
    property_id: propertyId,
  })

  const { data: items = [], isLoading } = useQuery<InventoryItem[]>({
    queryKey: ['inventory', propertyId, filterCategory, showLowStockOnly],
    enabled: !!propertyId,
    queryFn: async () => {
      const params = new URLSearchParams()
      if (propertyId) params.set('property_id', propertyId)
      if (filterCategory) params.set('category', filterCategory)
      if (showLowStockOnly) params.set('low_stock_only', 'true')
      const { data } = await api.get(`/inventory/items?${params}`)
      return data
    },
  })

  const addItemMutation = useMutation({
    mutationFn: (data: typeof newItem) => api.post('/inventory/items', {
      ...data,
      unit_cost: data.unit_cost ? Number(data.unit_cost) : undefined,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inventory'] })
      setShowAddModal(false)
      toast.success('Item added')
    },
  })

  const updateItemMutation = useMutation({
    mutationFn: () =>
      api.patch(`/inventory/items/${editItem!.id}`, {
        item_name: editForm.item_name,
        minimum_stock: editForm.minimum_stock,
        unit_cost: editForm.unit_cost ? Number(editForm.unit_cost) : undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inventory'] })
      setShowEditModal(false)
      toast.success('Item updated')
    },
  })

  const deleteItemMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/inventory/items/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inventory'] })
      toast.success('Item deactivated')
    },
  })

  const photoMutation = useMutation({
    mutationFn: ({ id, file }: { id: string; file: File }) => {
      const fd = new FormData()
      fd.append('file', file)
      return api.post(`/inventory/items/${id}/photo`, fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inventory'] })
      toast.success('Photo uploaded')
    },
  })

  const transactionMutation = useMutation({
    mutationFn: (data: { inventory_item_id: string; transaction_type: string; quantity: number; notes?: string }) =>
      api.post('/inventory/transactions', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inventory'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      setShowTransactionModal(false)
      toast.success(`Stock ${transactionType === 'IN' ? 'added' : 'deducted'} successfully`)
    },
    onError: (err: unknown) => {
      const error = err as { response?: { data?: { detail?: string } } }
      toast.error(error.response?.data?.detail || 'Transaction failed')
    },
  })

  const filtered = items.filter(item =>
    item.item_name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const lowStockCount = items.filter(i => i.is_low_stock).length

  if (isLoading) return <PageLoader />

  return (
    <RequirePropertyScope>
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Inventory</h1>
          <p className="text-gray-500 text-sm">{items.length} items • {lowStockCount} low stock alerts</p>
        </div>
        <button onClick={() => setShowAddModal(true)} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" />
          Add Item
        </button>
      </div>

      {lowStockCount > 0 && (
        <div
          className="mb-4 p-4 bg-yellow-50 border border-yellow-200 rounded-xl flex items-center gap-3 cursor-pointer hover:bg-yellow-100 transition-colors"
          onClick={() => setShowLowStockOnly(!showLowStockOnly)}
        >
          <AlertTriangle className="w-5 h-5 text-yellow-600 flex-shrink-0" />
          <p className="text-sm text-yellow-800">
            <span className="font-semibold">{lowStockCount} items</span> are running low on stock.{' '}
            <span className="underline">{showLowStockOnly ? 'Show all' : 'View low stock'}</span>
          </p>
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search items..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10 pr-4 py-2 border border-gray-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <select className="border border-gray-200 rounded-lg px-3 py-2 text-sm bg-white" value={filterCategory} onChange={(e) => setFilterCategory(e.target.value)}>
          <option value="">All Categories</option>
          {CATEGORIES.map(c => <option key={c}>{c}</option>)}
        </select>
        <label className="flex items-center gap-2 text-sm cursor-pointer">
          <input type="checkbox" checked={showLowStockOnly} onChange={(e) => setShowLowStockOnly(e.target.checked)} className="rounded border-gray-300 text-blue-600" />
          Low stock only
        </label>
      </div>

      {/* Items table */}
      <div className="table-container">
        <table className="w-full">
          <thead className="table-header">
            <tr>
              <th className="th">Item</th>
              <th className="th">Category</th>
              <th className="th">Stock</th>
              <th className="th">Min Stock</th>
              <th className="th">Unit Cost</th>
              <th className="th">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {filtered.map((item) => (
              <tr key={item.id} className="tr-hover">
                <td className="td">
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${item.is_low_stock ? 'bg-red-50' : 'bg-blue-50'}`}>
                      <Package className={`w-4 h-4 ${item.is_low_stock ? 'text-red-500' : 'text-blue-500'}`} />
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{item.item_name}</p>
                      {item.item_code && <p className="text-xs text-gray-400">{item.item_code}</p>}
                    </div>
                  </div>
                </td>
                <td className="td">
                  <span className="bg-gray-100 text-gray-700 text-xs px-2 py-1 rounded-full">{item.category}</span>
                </td>
                <td className="td">
                  <div className="flex items-center gap-2">
                    <span className={`font-semibold ${item.is_low_stock ? 'text-red-600' : 'text-gray-900'}`}>
                      {item.current_stock}
                    </span>
                    <span className="text-gray-400 text-xs">{item.unit}</span>
                    {item.is_low_stock && <AlertTriangle className="w-4 h-4 text-red-500" />}
                  </div>
                </td>
                <td className="td text-gray-500">{item.minimum_stock} {item.unit}</td>
                <td className="td text-gray-500">{item.unit_cost ? `₹${item.unit_cost}` : '-'}</td>
                <td className="td">
                  <div className="flex flex-wrap gap-1 items-center">
                    <button
                      onClick={() => {
                        setEditItem(item)
                        setEditForm({
                          item_name: item.item_name,
                          minimum_stock: item.minimum_stock,
                          unit_cost: item.unit_cost ? String(item.unit_cost) : '',
                        })
                        setShowEditModal(true)
                      }}
                      className="p-1.5 text-gray-500 hover:bg-gray-100 rounded"
                      title="Edit"
                    >
                      <Pencil className="w-3.5 h-3.5" />
                    </button>
                    <label className="p-1.5 text-blue-600 hover:bg-blue-50 rounded cursor-pointer" title="Photo">
                      <ImagePlus className="w-3.5 h-3.5" />
                      <input type="file" accept="image/*" className="hidden" onChange={e => {
                        const f = e.target.files?.[0]
                        if (f) photoMutation.mutate({ id: item.id, file: f })
                      }} />
                    </label>
                    <button
                      onClick={() => { if (confirm('Deactivate item?')) deleteItemMutation.mutate(item.id) }}
                      className="p-1.5 text-red-600 hover:bg-red-50 rounded"
                      title="Deactivate"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => { setSelectedItem(item); setTransactionType('IN'); setTransactionQty(1); setShowTransactionModal(true) }}
                      className="flex items-center gap-1 text-xs text-green-700 bg-green-50 hover:bg-green-100 px-2.5 py-1.5 rounded-lg font-medium transition-colors"
                    >
                      <ArrowUp className="w-3 h-3" />
                      Stock In
                    </button>
                    <button
                      onClick={() => { setSelectedItem(item); setTransactionType('OUT'); setTransactionQty(1); setShowTransactionModal(true) }}
                      className="flex items-center gap-1 text-xs text-red-700 bg-red-50 hover:bg-red-100 px-2.5 py-1.5 rounded-lg font-medium transition-colors"
                    >
                      <ArrowDown className="w-3 h-3" />
                      Stock Out
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {filtered.length === 0 && (
          <div className="text-center py-12 text-gray-400">
            <Package className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>No inventory items found</p>
          </div>
        )}
      </div>

      {/* Add Item Modal */}
      <Modal isOpen={showAddModal} onClose={() => setShowAddModal(false)} title="Add Inventory Item">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Item Name</label>
            <input className="input" value={newItem.item_name} onChange={(e) => setNewItem({ ...newItem, item_name: e.target.value })} placeholder="e.g., Bath Towels" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
              <select className="input" value={newItem.category} onChange={(e) => setNewItem({ ...newItem, category: e.target.value })}>
                {CATEGORIES.map(c => <option key={c}>{c}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Unit</label>
              <select className="input" value={newItem.unit} onChange={(e) => setNewItem({ ...newItem, unit: e.target.value })}>
                {['piece', 'kg', 'liter', 'box', 'roll', 'set', 'bottle', 'packet'].map(u => <option key={u}>{u}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Initial Stock</label>
              <input type="number" className="input" value={newItem.current_stock} onChange={(e) => setNewItem({ ...newItem, current_stock: Number(e.target.value) })} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Min Stock Alert</label>
              <input type="number" className="input" value={newItem.minimum_stock} onChange={(e) => setNewItem({ ...newItem, minimum_stock: Number(e.target.value) })} />
            </div>
            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">Unit Cost (₹)</label>
              <input type="number" className="input" value={newItem.unit_cost} onChange={(e) => setNewItem({ ...newItem, unit_cost: e.target.value })} placeholder="0.00" />
            </div>
          </div>
          <div className="flex gap-3 pt-2">
            <button onClick={() => setShowAddModal(false)} className="btn-secondary flex-1">Cancel</button>
            <button onClick={() => addItemMutation.mutate(newItem)} disabled={addItemMutation.isPending || !newItem.item_name} className="btn-primary flex-1">
              Add Item
            </button>
          </div>
        </div>
      </Modal>

      {editItem && (
        <Modal isOpen={showEditModal} onClose={() => setShowEditModal(false)} title={`Edit — ${editItem.item_name}`}>
          <div className="space-y-3">
            <input className="input" value={editForm.item_name} onChange={e => setEditForm({ ...editForm, item_name: e.target.value })} />
            <input type="number" className="input" value={editForm.minimum_stock} onChange={e => setEditForm({ ...editForm, minimum_stock: Number(e.target.value) })} placeholder="Min stock" />
            <input className="input" value={editForm.unit_cost} onChange={e => setEditForm({ ...editForm, unit_cost: e.target.value })} placeholder="Unit cost" />
            <button className="btn-primary w-full" onClick={() => updateItemMutation.mutate()}>Save</button>
          </div>
        </Modal>
      )}

      {/* Transaction Modal */}
      {selectedItem && (
        <Modal
          isOpen={showTransactionModal}
          onClose={() => setShowTransactionModal(false)}
          title={`${transactionType === 'IN' ? 'Stock In' : 'Stock Out'} - ${selectedItem.item_name}`}
        >
          <div className="space-y-4">
            <div className="p-3 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-500">Current Stock: <span className="font-semibold text-gray-900">{selectedItem.current_stock} {selectedItem.unit}</span></p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Quantity</label>
              <input
                type="number"
                min={1}
                max={transactionType === 'OUT' ? selectedItem.current_stock : undefined}
                className="input"
                value={transactionQty}
                onChange={(e) => setTransactionQty(Number(e.target.value))}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Notes (optional)</label>
              <input className="input" value={transactionNotes} onChange={(e) => setTransactionNotes(e.target.value)} placeholder="Reason or reference..." />
            </div>
            <div className="flex gap-3 pt-2">
              <button onClick={() => setShowTransactionModal(false)} className="btn-secondary flex-1">Cancel</button>
              <button
                onClick={() => transactionMutation.mutate({
                  inventory_item_id: selectedItem.id,
                  transaction_type: transactionType,
                  quantity: transactionQty,
                  notes: transactionNotes || undefined,
                })}
                disabled={transactionMutation.isPending || transactionQty < 1}
                className={transactionType === 'IN' ? 'btn-success flex-1' : 'btn-danger flex-1'}
              >
                {transactionType === 'IN' ? 'Add Stock' : 'Deduct Stock'}
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
    </RequirePropertyScope>
  )
}
