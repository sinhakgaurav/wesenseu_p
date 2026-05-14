import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import {
  CheckCircle, XCircle, Zap, Shield, Rocket, Star, Building2,
  ChevronDown,
} from 'lucide-react'
import api from '@/lib/api'
import { PublicNav } from '@/components/layout/PublicNav'

// ── Currency configuration ────────────────────────────────────────────────────

const CURRENCIES = [
  { code: 'INR', symbol: '₹', label: 'Indian Rupee',     flag: '🇮🇳', rate: 1       },
  { code: 'USD', symbol: '$', label: 'US Dollar',         flag: '🇺🇸', rate: 0.012   },
  { code: 'EUR', symbol: '€', label: 'Euro',              flag: '🇪🇺', rate: 0.011   },
  { code: 'GBP', symbol: '£', label: 'British Pound',     flag: '🇬🇧', rate: 0.0094  },
  { code: 'AED', symbol: 'د.إ', label: 'UAE Dirham',     flag: '🇦🇪', rate: 0.044   },
  { code: 'SGD', symbol: 'S$', label: 'Singapore Dollar', flag: '🇸🇬', rate: 0.016   },
  { code: 'SAR', symbol: '﷼',  label: 'Saudi Riyal',     flag: '🇸🇦', rate: 0.045   },
]

function convertPrice(inrAmount: number | null, rate: number): number | null {
  if (inrAmount == null) return null
  return Math.round(inrAmount * rate)
}

function formatPrice(amount: number | null, symbol: string, code: string): string {
  if (amount == null) return 'Custom'
  if (code === 'INR') return `${symbol}${amount.toLocaleString('en-IN')}`
  return `${symbol}${amount.toLocaleString('en-US')}`
}

// ── Plan icon map ─────────────────────────────────────────────────────────────

const PLAN_ICONS: Record<string, React.ReactNode> = {
  starter:    <Shield className="w-5 h-5" />,
  growth:     <Rocket className="w-5 h-5" />,
  enterprise: <Star className="w-5 h-5" />,
  custom:     <Building2 className="w-5 h-5" />,
}

const PLAN_COLORS: Record<string, { bg: string; icon: string; badge: string; cta: string; ring: string }> = {
  starter:    { bg: 'bg-white',                         icon: 'bg-gray-100 text-gray-600',   badge: '', cta: 'bg-gray-900 text-white hover:bg-gray-800', ring: 'border-gray-200' },
  growth:     { bg: 'bg-gradient-to-b from-blue-600 to-indigo-700', icon: 'bg-white/20 text-white',      badge: 'MOST POPULAR', cta: 'bg-white text-blue-700 hover:bg-blue-50', ring: 'border-transparent' },
  enterprise: { bg: 'bg-white',                         icon: 'bg-purple-100 text-purple-600', badge: '', cta: 'bg-purple-600 text-white hover:bg-purple-700', ring: 'border-purple-200' },
  custom:     { bg: 'bg-white',                         icon: 'bg-amber-100 text-amber-600',  badge: '', cta: 'bg-amber-500 text-white hover:bg-amber-600', ring: 'border-amber-200' },
}

// ── Feature comparison rows shown on every card ───────────────────────────────
// These define what each plan INCLUDES for the comparison highlights shown
// below the plan's own feature list.
const COMPARISON_FEATURES: Record<string, boolean[]> = {
  'Room management':           [true,  true,  true,  true ],
  'Task & ticket system':      [true,  true,  true,  true ],
  'Guest portal (QR)':         [true,  true,  true,  true ],
  'Inventory & orders':        [false, true,  true,  true ],
  'Attendance tracking':       [false, true,  true,  true ],
  'AI room verification':      [false, true,  true,  true ],
  'CCTV surveillance':         [false, true,  true,  true ],
  'Multi-property dashboard':  [false, false, true,  true ],
  'AI customer support chat':  [false, false, true,  true ],
  'White-label & IoT':         [false, false, false, true ],
}

const PLAN_ORDER = ['starter', 'growth', 'enterprise', 'custom']

// Enrich API plan with the per-slug comparison rows
function enrichPlan(plan: any, slugIndex: number) {
  const apiFeatures: string[] = Array.isArray(plan.features)
    ? plan.features.map((f: any) => (typeof f === 'string' ? f : f.label))
    : []

  // Build { label, included } list from comparison matrix
  const compFeatures = Object.entries(COMPARISON_FEATURES).map(([label, vals]) => ({
    label,
    included: vals[slugIndex] ?? false,
  }))

  return { ...plan, features: apiFeatures, compFeatures }
}

// Normalise plan ordering by slug
function sortPlans(plans: any[]) {
  return [...plans].sort((a, b) => {
    const ia = PLAN_ORDER.indexOf(a.slug)
    const ib = PLAN_ORDER.indexOf(b.slug)
    return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib)
  })
}

// ── Currency Selector ─────────────────────────────────────────────────────────

function CurrencySelector({
  value, onChange,
}: { value: string; onChange: (code: string) => void }) {
  const [open, setOpen] = useState(false)
  const selected = CURRENCIES.find(c => c.code === value) ?? CURRENCIES[0]

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(v => !v)}
        className="flex items-center gap-2 border border-gray-200 rounded-xl px-3 py-2 text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors shadow-sm"
      >
        <span className="text-base">{selected.flag}</span>
        <span>{selected.code}</span>
        <span className="text-gray-400 text-xs">{selected.symbol}</span>
        <ChevronDown className={`w-3.5 h-3.5 text-gray-400 transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <div className="absolute right-0 top-full mt-2 z-20 bg-white border border-gray-100 rounded-2xl shadow-xl overflow-hidden min-w-[200px]">
            {CURRENCIES.map(c => (
              <button
                key={c.code}
                onClick={() => { onChange(c.code); setOpen(false) }}
                className={`w-full flex items-center gap-3 px-4 py-2.5 text-sm hover:bg-gray-50 transition-colors ${
                  c.code === value ? 'bg-blue-50 text-blue-700 font-semibold' : 'text-gray-700'
                }`}
              >
                <span className="text-base">{c.flag}</span>
                <span className="font-medium">{c.code}</span>
                <span className="text-gray-400 flex-1 text-right text-xs">{c.label}</span>
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  )
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export function PricingPage() {
  const [billing, setBilling] = useState<'monthly' | 'yearly'>('monthly')
  const [currencyCode, setCurrencyCode] = useState('INR')

  const currency = CURRENCIES.find(c => c.code === currencyCode) ?? CURRENCIES[0]

  const { data: rawPlans, isLoading, isError } = useQuery({
    queryKey: ['public-plans'],
    queryFn: () => api.get('/plans').then(r => r.data),
    staleTime: 5 * 60 * 1000,
    retry: 2,
  })

  const plans = sortPlans(rawPlans ?? []).map((p: any, i: number) => enrichPlan(p, i))

  const getPrice = (plan: any) => {
    const base = billing === 'yearly' ? plan.price_yearly : plan.price_monthly
    return convertPrice(base, currency.rate)
  }

  const getSavingsPct = (plan: any) => {
    if (!plan.price_monthly || !plan.price_yearly) return 0
    return Math.round(100 - plan.price_yearly / (plan.price_monthly * 12) * 100)
  }

  return (
    <div className="min-h-screen bg-white">
      <PublicNav />

      {/* Hero */}
      <section className="pt-16 pb-10 bg-gradient-to-b from-blue-50/60 to-white">
        <div className="max-w-3xl mx-auto px-6 text-center">
          <div className="inline-flex items-center gap-2 bg-green-100 text-green-700 text-xs font-semibold px-3 py-1.5 rounded-full mb-5">
            <Zap className="w-3.5 h-3.5" /> 14-day free trial · No credit card required
          </div>
          <h1 className="text-4xl sm:text-5xl font-extrabold text-gray-900 tracking-tight mb-4">
            Simple, Transparent Pricing
          </h1>
          <p className="text-lg text-gray-500 mb-8">
            Choose the plan that fits your property. Scale as you grow.
          </p>

          {/* Controls row */}
          <div className="flex items-center justify-center gap-4 flex-wrap">
            {/* Billing toggle */}
            <div className="flex items-center bg-gray-100 rounded-xl p-1 gap-1">
              <button
                onClick={() => setBilling('monthly')}
                className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${
                  billing === 'monthly' ? 'bg-white shadow text-gray-900' : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Monthly
              </button>
              <button
                onClick={() => setBilling('yearly')}
                className={`flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${
                  billing === 'yearly' ? 'bg-white shadow text-gray-900' : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Yearly
                <span className="bg-green-100 text-green-700 text-xs font-bold px-1.5 py-0.5 rounded-md">
                  Save 17%
                </span>
              </button>
            </div>

            {/* Currency selector */}
            <CurrencySelector value={currencyCode} onChange={setCurrencyCode} />
          </div>
        </div>
      </section>

      {/* Pricing tiles */}
      <section className="py-10 max-w-7xl mx-auto px-6">
        {/* Loading skeleton */}
        {isLoading && (
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {[1,2,3,4].map(i => (
              <div key={i} className="rounded-2xl border-2 border-gray-100 p-6 animate-pulse">
                <div className="w-10 h-10 bg-gray-200 rounded-xl mb-4" />
                <div className="h-5 bg-gray-200 rounded w-1/2 mb-2" />
                <div className="h-3 bg-gray-100 rounded w-3/4 mb-6" />
                <div className="h-10 bg-gray-200 rounded w-2/3 mb-6" />
                {[1,2,3,4,5].map(j => (
                  <div key={j} className="h-3 bg-gray-100 rounded mb-2" />
                ))}
                <div className="h-10 bg-gray-200 rounded mt-6" />
              </div>
            ))}
          </div>
        )}

        {/* Error state */}
        {isError && !isLoading && (
          <div className="text-center py-12 text-gray-400">
            <p className="text-lg font-medium text-gray-500 mb-1">Unable to load plans</p>
            <p className="text-sm">Please refresh the page or contact support.</p>
          </div>
        )}

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {!isLoading && plans.map((plan: any) => {
            const price = getPrice(plan)
            const savings = getSavingsPct(plan)
            const colors = PLAN_COLORS[plan.slug] ?? PLAN_COLORS.starter
            const isPopular = plan.is_popular
            const isLight = plan.slug === 'growth'

            return (
              <div
                key={plan.id || plan.slug}
                className={`relative rounded-2xl border-2 flex flex-col overflow-hidden transition-shadow hover:shadow-xl ${colors.bg} ${colors.ring} ${
                  isPopular ? 'shadow-2xl shadow-blue-200/60 scale-[1.02]' : 'shadow-sm'
                }`}
              >
                {/* Popular badge */}
                {colors.badge && (
                  <div className={`absolute top-4 right-4 text-xs font-extrabold px-2.5 py-1 rounded-full tracking-wide ${
                    isLight ? 'bg-white/20 text-white' : 'bg-blue-100 text-blue-700'
                  }`}>
                    {colors.badge}
                  </div>
                )}

                <div className="p-6 flex flex-col flex-1">
                  {/* Plan header */}
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center mb-4 ${colors.icon}`}>
                    {PLAN_ICONS[plan.slug] ?? <Shield className="w-5 h-5" />}
                  </div>

                  <h3 className={`text-lg font-bold mb-1 ${isLight ? 'text-white' : 'text-gray-900'}`}>
                    {plan.name}
                  </h3>
                  <p className={`text-xs mb-5 leading-relaxed ${isLight ? 'text-blue-100' : 'text-gray-500'}`}>
                    {plan.tagline}
                  </p>

                  {/* Price */}
                  <div className="mb-1">
                    {price != null ? (
                      <div className="flex items-end gap-1">
                        <span className={`text-4xl font-extrabold tracking-tight ${isLight ? 'text-white' : 'text-gray-900'}`}>
                          {formatPrice(price, currency.symbol, currencyCode)}
                        </span>
                        <span className={`text-sm mb-1.5 ${isLight ? 'text-blue-200' : 'text-gray-400'}`}>
                          /{billing === 'yearly' ? 'yr' : 'mo'}
                        </span>
                      </div>
                    ) : (
                      <span className={`text-3xl font-extrabold ${isLight ? 'text-white' : 'text-gray-900'}`}>
                        Custom
                      </span>
                    )}
                  </div>

                  {/* Yearly savings note */}
                  {billing === 'yearly' && savings > 0 && (
                    <p className={`text-xs font-medium mb-4 ${isLight ? 'text-green-200' : 'text-green-600'}`}>
                      You save {savings}% vs monthly billing
                    </p>
                  )}
                  {billing === 'monthly' && plan.price_yearly && (
                    <p className={`text-xs mb-4 ${isLight ? 'text-blue-200' : 'text-gray-400'}`}>
                      {formatPrice(convertPrice(plan.price_yearly, currency.rate), currency.symbol, currencyCode)}/yr if billed annually
                    </p>
                  )}
                  {!plan.price_monthly && !plan.price_yearly && (
                    <p className={`text-xs mb-4 ${isLight ? 'text-blue-200' : 'text-gray-400'}`}>
                      Pricing tailored to your scale
                    </p>
                  )}

                  {/* Room / staff limits */}
                  <div className={`flex gap-3 mb-5 text-xs ${isLight ? 'text-blue-100' : 'text-gray-500'}`}>
                    {plan.room_limit && (
                      <span className={`px-2 py-1 rounded-lg ${isLight ? 'bg-white/15' : 'bg-gray-100'}`}>
                        Up to {plan.room_limit} rooms
                      </span>
                    )}
                    {plan.employee_limit && (
                      <span className={`px-2 py-1 rounded-lg ${isLight ? 'bg-white/15' : 'bg-gray-100'}`}>
                        {plan.employee_limit} staff
                      </span>
                    )}
                    {!plan.room_limit && (
                      <span className={`px-2 py-1 rounded-lg ${isLight ? 'bg-white/15' : 'bg-gray-100'}`}>
                        Unlimited
                      </span>
                    )}
                  </div>

                  {/* Plan-specific features from DB */}
                  {plan.features.length > 0 && (
                    <ul className="space-y-1.5 mb-4 border-b border-black/10 pb-4">
                      {plan.features.map((label: string, i: number) => (
                        <li key={i} className={`flex items-start gap-2 text-xs ${isLight ? 'text-blue-50' : 'text-gray-700'}`}>
                          <CheckCircle className={`w-3.5 h-3.5 flex-shrink-0 mt-0.5 ${isLight ? 'text-green-300' : 'text-green-500'}`} />
                          {label}
                        </li>
                      ))}
                    </ul>
                  )}

                  {/* Comparison feature rows */}
                  <ul className="space-y-1.5 flex-1 mb-6">
                    {(plan.compFeatures ?? []).map((f: { label: string; included: boolean }, i: number) => (
                      <li key={i} className={`flex items-start gap-2 text-xs ${
                        f.included
                          ? isLight ? 'text-blue-100' : 'text-gray-600'
                          : isLight ? 'text-blue-300/40 line-through' : 'text-gray-300 line-through'
                      }`}>
                        {f.included ? (
                          <CheckCircle className={`w-3.5 h-3.5 flex-shrink-0 mt-0.5 ${isLight ? 'text-green-300' : 'text-green-500'}`} />
                        ) : (
                          <XCircle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5 text-gray-300" />
                        )}
                        {f.label}
                      </li>
                    ))}
                  </ul>

                  {/* CTA */}
                  <Link
                    to={plan.slug === 'custom' ? '/contact' : '/login'}
                    className={`text-center py-3 rounded-xl font-semibold text-sm transition-all hover:scale-[1.02] active:scale-[0.98] ${colors.cta}`}
                  >
                    {plan.cta_text}
                  </Link>
                </div>
              </div>
            )
          })}
        </div>

        {/* Currency note */}
        {currencyCode !== 'INR' && (
          <p className="text-center text-xs text-gray-400 mt-6">
            * Prices shown in {currency.label} ({currencyCode}) are approximate conversions from INR for reference.
            Final billing is in INR.
          </p>
        )}
      </section>

      {/* Feature comparison table */}
      <section className="py-14 bg-gray-50">
        <div className="max-w-5xl mx-auto px-6">
          <h2 className="text-2xl font-bold text-gray-900 text-center mb-2">Compare Plans</h2>
          <p className="text-center text-sm text-gray-500 mb-10">Everything you get across all plans</p>

          <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-100">
                    <th className="text-left px-6 py-4 text-gray-500 font-medium w-1/3">Feature</th>
                    {['Starter', 'Growth', 'Enterprise', 'Custom'].map(n => (
                      <th key={n} className={`px-4 py-4 font-bold text-center ${n === 'Growth' ? 'text-blue-600' : 'text-gray-900'}`}>
                        {n}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {[
                    { label: 'Room management',           vals: [true, true, true, true] },
                    { label: 'Task & ticket system',      vals: [true, true, true, true] },
                    { label: 'Guest portal (QR)',          vals: [true, true, true, true] },
                    { label: 'Inventory management',      vals: [false, true, true, true] },
                    { label: 'Orders / room service',     vals: [false, true, true, true] },
                    { label: 'Attendance tracking',       vals: [false, true, true, true] },
                    { label: 'AI room verification',      vals: [false, true, true, true] },
                    { label: 'CCTV surveillance',         vals: [false, true, true, true] },
                    { label: 'Benchmark management',      vals: [false, true, true, true] },
                    { label: 'Advanced analytics',        vals: [false, true, true, true] },
                    { label: 'Multi-property dashboard',  vals: [false, false, true, true] },
                    { label: 'AI customer support chat',  vals: [false, false, true, true] },
                    { label: 'White-label branding',      vals: [false, false, false, true] },
                    { label: 'IoT / Smart Lock',          vals: [false, false, false, true] },
                    { label: 'Dedicated infrastructure',  vals: [false, false, false, true] },
                    { label: 'SLA-backed support',        vals: [false, false, false, true] },
                  ].map(({ label, vals }) => (
                    <tr key={label} className="border-b border-gray-50 hover:bg-gray-50/50 transition-colors">
                      <td className="px-6 py-3 text-gray-700">{label}</td>
                      {vals.map((v, i) => (
                        <td key={i} className="px-4 py-3 text-center">
                          {v
                            ? <CheckCircle className="w-4 h-4 text-green-500 mx-auto" />
                            : <XCircle className="w-4 h-4 text-gray-200 mx-auto" />
                          }
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="py-16 max-w-3xl mx-auto px-6">
        <h2 className="text-2xl font-bold text-gray-900 text-center mb-10">Frequently Asked Questions</h2>
        <div className="space-y-3">
          {[
            { q: 'Is there a free trial?',
              a: 'Yes — all plans include a 14-day free trial. No credit card required to start.' },
            { q: 'Can I change plans later?',
              a: 'Absolutely. You can upgrade or downgrade at any time from your account settings.' },
            { q: 'What currencies do you accept?',
              a: 'Billing is processed in INR. The currency selector on this page shows approximate conversions for reference.' },
            { q: 'Do you support hospitals and clinics?',
              a: 'Yes! Monitour works for any property-type — hotels, hospitals, co-living spaces, or corporate campuses.' },
            { q: 'What is WesenseU?',
              a: 'WesenseU is our AI microservice. It compares staff room photos against your benchmark images and scores cleanliness, organisation, and amenity completeness.' },
            { q: 'What happens after the free trial?',
              a: "You'll be prompted to select a paid plan. If you don't upgrade, your account is paused (data is retained for 30 days)." },
          ].map(({ q, a }) => (
            <details key={q} className="bg-gray-50 rounded-xl border border-gray-100 p-4 group cursor-pointer">
              <summary className="font-medium text-gray-900 list-none flex justify-between items-center gap-4">
                {q}
                <ChevronDown className="w-4 h-4 text-gray-400 flex-shrink-0 group-open:rotate-180 transition-transform" />
              </summary>
              <p className="text-gray-500 text-sm mt-3 leading-relaxed">{a}</p>
            </details>
          ))}
        </div>
      </section>

      {/* Bottom CTA */}
      <section className="bg-gradient-to-r from-blue-600 to-indigo-700 py-16">
        <div className="max-w-2xl mx-auto px-6 text-center">
          <h2 className="text-3xl font-bold text-white mb-3">Ready to get started?</h2>
          <p className="text-blue-100 mb-8">
            Join hundreds of properties using Monitour to streamline operations.
          </p>
          <div className="flex items-center justify-center gap-4 flex-wrap">
            <Link to="/login" className="bg-white text-blue-700 font-semibold px-6 py-3 rounded-xl hover:bg-blue-50 transition-colors">
              Start 14-day Free Trial
            </Link>
            <Link to="/contact" className="border border-white/40 text-white font-semibold px-6 py-3 rounded-xl hover:bg-white/10 transition-colors">
              Talk to Sales
            </Link>
          </div>
        </div>
      </section>
    </div>
  )
}
