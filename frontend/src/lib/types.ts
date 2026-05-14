export type UserRole = 'super_admin' | 'property_manager' | 'dept_manager' | 'employee' | 'guest'

export interface User {
  id: string
  full_name: string
  email: string
  role: UserRole
  property_id: string | null
  department_id: string | null
  avatar_url: string | null
  employee_code: string
}

export interface Property {
  id: string
  name: string
  property_type: string
  address?: string
  city?: string
  state?: string
  country: string
  phone?: string
  email?: string
  total_rooms: number
  subscription_plan: string
  subscription_status: string
  is_active: boolean
  created_at: string
  customer_id?: string | null
  property_group_id?: string | null
  parent_property_id?: string | null
}

export interface PropertyRoomCategory {
  id: string
  property_id: string
  code: string
  display_name: string
  description?: string | null
  sort_order: number
  is_active: boolean
  created_at: string
}

export interface PropertyGroup {
  id: string
  customer_id?: string | null
  name: string
  description?: string | null
  parent_group_id?: string | null
  is_active: boolean
  created_at: string
}

export interface Department {
  id: string
  property_id: string
  name: string
  description?: string
  manager_id?: string | null
  is_active: boolean
  created_at?: string
}

export interface Employee {
  id: string
  property_id: string
  department_id?: string
  employee_code: string
  full_name: string
  role: UserRole
  phone?: string
  email: string
  shift_type?: string
  joining_date?: string
  salary?: number
  status: 'active' | 'inactive' | 'suspended'
  is_available: boolean
  avatar_url?: string
  created_at: string
}

export type RoomStatus =
  | 'occupied'
  | 'vacant'
  | 'cleaning_pending'
  | 'cleaning_in_progress'
  | 'ready'
  | 'maintenance'
  | 'inspection_pending'
  | 'blocked'

export interface Room {
  id: string
  property_id: string
  room_number: string
  room_category: string
  property_room_category_id?: string | null
  floor_number?: number
  room_status: RoomStatus
  occupancy_status: 'occupied' | 'vacant'
  guest_name?: string
  guest_phone?: string
  check_in_time?: string
  check_out_time?: string
  expected_check_out?: string
  last_cleaned_at?: string
  qr_code_url?: string
  is_active: boolean
  created_at: string
}

export type TaskStatus =
  | 'pending'
  | 'assigned'
  | 'in_progress'
  | 'verification_pending'
  | 'approved'
  | 'rejected'
  | 'rework_required'
  | 'completed'
  | 'cancelled'

export interface Task {
  id: string
  property_id: string
  room_id?: string
  assigned_to?: string
  created_by?: string
  ticket_id?: string
  task_type: string
  service_type?: string
  priority: 'low' | 'medium' | 'high' | 'critical'
  status: TaskStatus
  description?: string
  due_time?: string
  sla_due_at?: string
  root_cause_category?: string
  sla_breached_at?: string
  started_at?: string
  completed_at?: string
  verification_required: boolean
  escalation_count: number
  media: TaskMedia[]
  created_at: string
}

export interface TaskMedia {
  id: string
  task_id: string
  media_url: string
  media_type: 'photo' | 'video'
  uploaded_by: string
  uploaded_at: string
}

export interface Ticket {
  id: string
  ticket_number: string
  property_id: string
  room_id?: string
  department_id?: string
  assigned_to?: string
  ticket_type: string
  priority: 'low' | 'medium' | 'high' | 'critical'
  status: string
  title: string
  description?: string
  guest_name?: string
  guest_phone?: string
  created_by_guest: boolean
  resolution_notes?: string
  sla_deadline?: string
  resolved_at?: string
  escalation_count: number
  rating?: number
  comments: TicketComment[]
  created_at: string
}

export interface TicketComment {
  id: string
  ticket_id: string
  author_name?: string
  comment: string
  is_internal: boolean
  created_at: string
}

export interface InventoryItem {
  id: string
  property_id: string
  item_name: string
  item_code?: string
  category: string
  unit: string
  current_stock: number
  minimum_stock: number
  unit_cost?: number
  vendor_id?: string
  is_active: boolean
  is_low_stock: boolean
  created_at: string
}

export interface Notification {
  id: string
  notification_type: string
  title: string
  message: string
  data?: Record<string, unknown>
  is_read: boolean
  created_at: string
}

export interface DashboardStats {
  total_rooms: number
  occupied_rooms: number
  vacant_rooms: number
  cleaning_pending: number
  ready_rooms: number
  maintenance_rooms: number
  active_tasks: number
  pending_tasks: number
  completed_tasks_today: number
  overdue_tasks: number
  open_tickets: number
  resolved_tickets_today: number
  critical_tickets: number
  total_employees: number
  available_employees: number
  employees_on_duty: number
  inventory_alerts: number
  surveillance_alerts: number
  room_status_chart: { status: string; count: number; label: string }[]
  task_completion_rate: number
  avg_ticket_resolution_time?: number
}
