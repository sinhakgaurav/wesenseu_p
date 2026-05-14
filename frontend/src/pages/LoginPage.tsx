import { useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { useNavigate } from 'react-router-dom'
import { Shield, Eye, EyeOff, Mail, Lock } from 'lucide-react'
import { login, clearError } from '@/store/authSlice'
import type { AppDispatch, RootState } from '@/store'

export function LoginPage() {
  const dispatch = useDispatch<AppDispatch>()
  const navigate = useNavigate()
  const { loading, error } = useSelector((state: RootState) => state.auth)

  const [form, setForm] = useState({ email: '', password: '' })
  const [showPassword, setShowPassword] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const result = await dispatch(login(form))
    if (login.fulfilled.match(result)) {
      navigate('/admin/dashboard')
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-blue-800 to-indigo-900 flex items-center justify-center p-4">
      {/* Background decorative elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-blue-500/10 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-indigo-500/10 rounded-full blur-3xl" />
      </div>

      <div className="relative w-full max-w-md">
        {/* Card */}
        <div className="bg-white rounded-2xl shadow-2xl overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-600 to-indigo-600 px-8 pt-10 pb-8 text-center">
            <div className="w-16 h-16 bg-white/20 rounded-2xl flex items-center justify-center mx-auto mb-4 backdrop-blur-sm">
              <Shield className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-white">Monitour</h1>
            <p className="text-blue-100 text-sm mt-1">AI-Powered Operations Platform</p>
          </div>

          {/* Form */}
          <div className="px-8 py-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-1">Welcome back</h2>
            <p className="text-sm text-gray-500 mb-6">Sign in to your account</p>

            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Email / Mobile</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    type="text"
                    value={form.email}
                    onChange={(e) => { setForm({ ...form, email: e.target.value }); dispatch(clearError()) }}
                    placeholder="you@example.com"
                    className="input pl-10"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Password</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={form.password}
                    onChange={(e) => { setForm({ ...form, password: e.target.value }); dispatch(clearError()) }}
                    placeholder="••••••••"
                    className="input pl-10 pr-10"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
                  <input type="checkbox" className="rounded border-gray-300 text-blue-600" />
                  Remember me
                </label>
                <a href="#" className="text-sm text-blue-600 hover:text-blue-700 font-medium">Forgot password?</a>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="btn-primary w-full py-3 text-base"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Signing in...
                  </span>
                ) : 'Sign In'}
              </button>
            </form>

            {/* Demo credentials */}
            <div className="mt-6 p-4 bg-blue-50 rounded-xl border border-blue-100">
              <p className="text-xs font-semibold text-blue-700 mb-2">
                Demo Credentials — <span className="font-normal text-blue-500">click any row to fill</span>
              </p>
              <p className="text-xs text-blue-400 mb-3">
                Demo users are auto-created on backend startup. Manual seed: <code className="bg-blue-100 px-1 rounded">python -m app.db.init_db</code>
              </p>
              <div className="space-y-1.5">
                {[
                  { label: 'Super Admin',    role: 'Full platform control',    email: 'admin@monitour.in',        password: 'Admin@2026',     color: 'bg-purple-50 text-purple-800 border-purple-200' },
                  { label: 'Prop. Manager',  role: 'Property-level manager',   email: 'manager@grandpalace.com',  password: 'Manager@123',    color: 'bg-blue-50 text-blue-800 border-blue-200' },
                  { label: 'Dept. Manager',  role: 'Housekeeping dept head',   email: 'hk_head@grandpalace.com',  password: 'DeptHead@123',   color: 'bg-sky-50 text-sky-800 border-sky-200' },
                  { label: 'Employee',       role: 'Room-service staff',        email: 'priya@grandpalace.com',    password: 'Password@123',   color: 'bg-green-50 text-green-800 border-green-200' },
                ].map((cred) => (
                  <button
                    key={cred.email}
                    type="button"
                    onClick={() => { setForm({ email: cred.email, password: cred.password }); dispatch(clearError()) }}
                    className={`w-full text-left px-3 py-2 rounded-lg border text-xs transition-all hover:opacity-80 active:scale-[0.98] ${cred.color}`}
                  >
                    <span className="font-semibold">{cred.label}</span>
                    <span className="mx-1.5 opacity-30">·</span>
                    <span className="opacity-70">{cred.role}</span>
                    <div className="mt-0.5 font-mono opacity-80">
                      {cred.email} / {cred.password}
                    </div>
                  </button>
                ))}
              </div>
              <div className="mt-3 pt-2 border-t border-blue-200">
                <p className="text-xs text-blue-500 font-medium mb-1">Customer Portal</p>
                <button
                  type="button"
                  onClick={() => window.open('/support', '_blank')}
                  className="w-full text-left px-3 py-2 rounded-lg border border-amber-200 bg-amber-50 text-amber-800 text-xs transition-all hover:opacity-80"
                >
                  <span className="font-semibold">Customer</span>
                  <span className="mx-1.5 opacity-30">·</span>
                  <span className="opacity-70">AI Support Chat & Pricing</span>
                  <div className="mt-0.5 font-mono opacity-70">customer@grandpalace.com / Customer@123</div>
                </button>
              </div>
            </div>
          </div>
        </div>

        <p className="text-center text-blue-200/60 text-xs mt-6">
          © 2026 Monitour. AI-Powered Operations Platform.
        </p>
      </div>
    </div>
  )
}
