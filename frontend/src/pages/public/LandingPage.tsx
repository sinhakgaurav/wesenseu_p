import { Link } from 'react-router-dom'
import { BedDouble, Camera, ClipboardList, Shield, BarChart2, Users, Zap, CheckCircle } from 'lucide-react'
import { PublicNav } from '@/components/layout/PublicNav'

const features = [
  { icon: BedDouble, title: 'Smart Room Management', desc: 'Full lifecycle tracking — check-in to verified clean, with AI room inspection.', color: 'blue' },
  { icon: Camera, title: 'CCTV Surveillance', desc: 'AI-powered anomaly detection from your existing IP cameras over WiFi.', color: 'purple' },
  { icon: ClipboardList, title: 'Task & Ticketing', desc: 'Assign housekeeping tasks, track SLAs, escalate open tickets automatically.', color: 'green' },
  { icon: Shield, title: 'AI Room Verification', desc: 'WesenseU compares staff photos against benchmark images for quality assurance.', color: 'orange' },
  { icon: BarChart2, title: 'Analytics & Reports', desc: 'Occupancy, task completion, ticket SLA, revenue, and staff performance.', color: 'teal' },
  { icon: Users, title: 'Multi-Role Access', desc: 'Super admin, property manager, department manager, staff and customer portals.', color: 'pink' },
]

const stats = [
  { value: '500+', label: 'Properties' },
  { value: '12k+', label: 'Rooms Managed' },
  { value: '99.9%', label: 'Uptime' },
  { value: '4.8★', label: 'Avg Rating' },
]

export function LandingPage() {
  return (
    <div className="min-h-screen bg-white">
      <PublicNav />

      {/* Hero */}
      <section className="bg-gradient-to-br from-blue-50 via-white to-indigo-50 pt-20 pb-24">
        <div className="max-w-5xl mx-auto px-6 text-center">
          <div className="inline-flex items-center gap-2 bg-blue-100 text-blue-700 text-xs font-semibold px-3 py-1 rounded-full mb-6">
            <Zap className="w-3 h-3" /> Powered by WesenseU AI
          </div>
          <h1 className="text-5xl md:text-6xl font-extrabold text-gray-900 leading-tight mb-6">
            The Hospitality OS<br className="hidden md:block" />
            <span className="text-blue-600"> Built for Modern Teams</span>
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto mb-10">
            From rooms and housekeeping to CCTV surveillance and AI inspections —
            Monitour gives your team everything in one place.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/contact" className="bg-blue-600 text-white px-8 py-3.5 rounded-xl font-semibold text-base hover:bg-blue-700 shadow-lg shadow-blue-200">
              Book a Demo
            </Link>
            <Link to="/pricing" className="bg-white text-gray-800 border border-gray-200 px-8 py-3.5 rounded-xl font-semibold text-base hover:border-blue-300">
              View Plans
            </Link>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="border-y border-gray-100 bg-gray-50/50">
        <div className="max-w-4xl mx-auto px-6 py-10 grid grid-cols-2 md:grid-cols-4 gap-8">
          {stats.map(s => (
            <div key={s.label} className="text-center">
              <p className="text-3xl font-extrabold text-blue-600">{s.value}</p>
              <p className="text-sm text-gray-500 mt-1">{s.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="py-24 max-w-7xl mx-auto px-6">
        <div className="text-center mb-14">
          <h2 className="text-3xl font-bold text-gray-900">Everything your property needs</h2>
          <p className="text-gray-500 mt-3">One platform. Zero scattered tools.</p>
        </div>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map(({ icon: Icon, title, desc, color }) => (
            <div key={title} className="p-6 rounded-2xl border border-gray-100 hover:border-blue-200 hover:shadow-md transition-all">
              <div className={`w-12 h-12 bg-${color}-50 rounded-xl flex items-center justify-center mb-4`}>
                <Icon className={`w-6 h-6 text-${color}-600`} />
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">{title}</h3>
              <p className="text-sm text-gray-500">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="bg-blue-600 py-20">
        <div className="max-w-3xl mx-auto px-6 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">Ready to modernise your operations?</h2>
          <p className="text-blue-100 mb-8">Start with a free trial or book a personalised demo.</p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/contact" className="bg-white text-blue-600 px-8 py-3.5 rounded-xl font-semibold hover:bg-blue-50">
              Book Demo
            </Link>
            <Link to="/pricing" className="border border-white/50 text-white px-8 py-3.5 rounded-xl font-semibold hover:bg-white/10">
              See Pricing
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-100 py-12 px-6">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-blue-600 rounded-lg flex items-center justify-center">
              <BedDouble className="w-3 h-3 text-white" />
            </div>
            <span className="font-bold text-gray-900">Monitour</span>
          </div>
          <div className="flex gap-6 text-sm text-gray-500">
            <Link to="/about" className="hover:text-blue-600">About</Link>
            <Link to="/pricing" className="hover:text-blue-600">Pricing</Link>
            <Link to="/contact" className="hover:text-blue-600">Contact</Link>
            <a href="mailto:support@monitour.in" className="hover:text-blue-600">support@monitour.in</a>
          </div>
          <p className="text-xs text-gray-400">© {new Date().getFullYear()} Monitour. All rights reserved.</p>
        </div>
      </footer>
    </div>
  )
}
