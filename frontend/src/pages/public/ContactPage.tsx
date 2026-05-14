import { useState } from 'react'
import { Mail, Phone, MapPin, MessageCircle } from 'lucide-react'
import toast from 'react-hot-toast'
import { PublicNav } from '@/components/layout/PublicNav'

export function ContactPage() {
  const [form, setForm] = useState({ name: '', email: '', company: '', message: '' })
  const [sending, setSending] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSending(true)
    await new Promise(r => setTimeout(r, 800))
    toast.success("Thanks! We'll be in touch within 24 hours.")
    setForm({ name: '', email: '', company: '', message: '' })
    setSending(false)
  }

  return (
    <div className="min-h-screen bg-white">
      <PublicNav />

      <section className="bg-gradient-to-br from-blue-50 to-white pt-20 pb-12">
        <div className="max-w-3xl mx-auto px-6 text-center">
          <h1 className="text-4xl font-extrabold text-gray-900 mb-4">Get in Touch</h1>
          <p className="text-gray-600">Book a demo, ask a question, or just say hello.</p>
        </div>
      </section>

      <section className="py-16 max-w-6xl mx-auto px-6">
        <div className="grid md:grid-cols-2 gap-12">
          {/* Contact info */}
          <div className="space-y-8">
            <div>
              <h2 className="text-xl font-bold text-gray-900 mb-6">Contact Information</h2>
              <div className="space-y-4">
                {[
                  { icon: Mail, label: 'Email', value: 'hello@monitour.in', href: 'mailto:hello@monitour.in' },
                  { icon: Phone, label: 'Phone', value: '+91 9000-000000', href: 'tel:+919000000000' },
                  { icon: MapPin, label: 'Address', value: 'Bandra Kurla Complex, Mumbai 400051', href: null },
                ].map(({ icon: Icon, label, value, href }) => (
                  <div key={label} className="flex items-start gap-4">
                    <div className="w-10 h-10 bg-blue-50 rounded-xl flex items-center justify-center flex-shrink-0">
                      <Icon className="w-5 h-5 text-blue-600" />
                    </div>
                    <div>
                      <p className="text-xs text-gray-400 font-medium uppercase tracking-wide">{label}</p>
                      {href ? (
                        <a href={href} className="text-gray-800 font-medium hover:text-blue-600">{value}</a>
                      ) : (
                        <p className="text-gray-800 font-medium">{value}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="p-5 bg-blue-50 rounded-2xl border border-blue-100">
              <div className="flex items-center gap-2 mb-2">
                <MessageCircle className="w-5 h-5 text-blue-600" />
                <span className="font-semibold text-gray-900 text-sm">Live Chat Support</span>
              </div>
              <p className="text-sm text-gray-600">Mon – Sat, 9 AM – 7 PM IST. Average response in under 2 minutes.</p>
            </div>

            <div>
              <h3 className="font-semibold text-gray-900 mb-3">Office Hours</h3>
              <div className="space-y-1 text-sm text-gray-600">
                <p>Monday – Friday: 9:00 AM – 7:00 PM IST</p>
                <p>Saturday: 10:00 AM – 4:00 PM IST</p>
                <p>Sunday: Closed (urgent issues via email)</p>
              </div>
            </div>
          </div>

          {/* Form */}
          <div className="card">
            <h2 className="text-xl font-bold text-gray-900 mb-6">Send us a message</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Full Name *</label>
                <input
                  required
                  type="text"
                  value={form.name}
                  onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                  className="input-field w-full"
                  placeholder="Rahul Sharma"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Work Email *</label>
                <input
                  required
                  type="email"
                  value={form.email}
                  onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
                  className="input-field w-full"
                  placeholder="rahul@hotel.com"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Company / Property Name</label>
                <input
                  type="text"
                  value={form.company}
                  onChange={e => setForm(f => ({ ...f, company: e.target.value }))}
                  className="input-field w-full"
                  placeholder="The Grand Hotel"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Message *</label>
                <textarea
                  required
                  rows={4}
                  value={form.message}
                  onChange={e => setForm(f => ({ ...f, message: e.target.value }))}
                  className="input-field w-full resize-none"
                  placeholder="Tell us about your property and what you're looking for..."
                />
              </div>
              <button
                type="submit"
                disabled={sending}
                className="btn-primary w-full"
              >
                {sending ? 'Sending...' : 'Send Message'}
              </button>
            </form>
          </div>
        </div>
      </section>
    </div>
  )
}
