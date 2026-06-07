import { Link } from 'react-router-dom'
import { Heart, Zap, Users } from 'lucide-react'
import { PublicNav } from '@/components/layout/PublicNav'
import { useCmsPage, htmlFromCmsPage } from '@/hooks/useCmsPage'
import { CmsPageHero, CmsHtmlBody } from '@/components/public/CmsPageHero'

const team = [
  { name: 'Arjun Mehta', role: 'Co-founder & CEO', bio: 'Former GM at a 5-star hotel chain with 12 years of ops experience.' },
  { name: 'Priya Sharma', role: 'Co-founder & CTO', bio: 'AI researcher with expertise in computer vision and facility management.' },
  { name: 'Ravi Nair', role: 'Head of Product', bio: 'Built hospitality software for 8+ years across Asia Pacific.' },
]

const values = [
  { icon: Heart, title: 'Hospitality First', desc: 'Every feature is built with the end guest experience in mind.' },
  { icon: Zap, title: 'AI-Powered Simplicity', desc: 'Complex analysis presented as clear, actionable insights.' },
  { icon: Users, title: 'Team Enablement', desc: 'Tools that empower every role — from housekeeping to GM.' },
]

export function AboutPage() {
  const { data: cmsPage } = useCmsPage('about')
  const cmsHtml = htmlFromCmsPage(cmsPage ?? undefined)

  return (
    <div className="min-h-screen bg-white">
      <PublicNav />

      <CmsPageHero
        page={cmsPage}
        fallbackTitle="About Monitour"
        fallbackSubtitle="We're on a mission to give every hospitality team the technology that was once reserved for global chains."
      />

      {cmsHtml ? (
        <CmsHtmlBody html={cmsHtml} />
      ) : (
        <>
          <section className="py-16 max-w-3xl mx-auto px-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Our Story</h2>
            <div className="prose text-gray-600 space-y-4">
              <p>
                Monitour was born out of frustration. Our founders spent years in hotel operations watching
                managers juggle WhatsApp groups, paper checklists, and Excel sheets to run multi-floor properties.
                Staff lost track of tasks, guest complaints went unresolved, and room verification was always subjective.
              </p>
              <p>
                In 2023, we decided to build the operating system we always wished existed — one that combines
                task management, AI room inspection, CCTV surveillance analysis, ticketing, and inventory
                into a single platform every team member can use.
              </p>
              <p>
                Today, Monitour powers 500+ properties across India, helping teams deliver consistent,
                data-backed quality at every touchpoint.
              </p>
            </div>
          </section>

          <section className="py-16 bg-gray-50">
            <div className="max-w-5xl mx-auto px-6">
              <h2 className="text-2xl font-bold text-gray-900 text-center mb-10">What we believe</h2>
              <div className="grid md:grid-cols-3 gap-8">
                {values.map(({ icon: Icon, title, desc }) => (
                  <div key={title} className="text-center">
                    <div className="w-12 h-12 bg-blue-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                      <Icon className="w-6 h-6 text-blue-600" />
                    </div>
                    <h3 className="font-semibold text-gray-900 mb-2">{title}</h3>
                    <p className="text-sm text-gray-500">{desc}</p>
                  </div>
                ))}
              </div>
            </div>
          </section>

          <section className="py-16 max-w-5xl mx-auto px-6">
            <h2 className="text-2xl font-bold text-gray-900 text-center mb-10">The Team</h2>
            <div className="grid md:grid-cols-3 gap-8">
              {team.map(person => (
                <div key={person.name} className="text-center p-6 rounded-2xl border border-gray-100">
                  <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4 text-2xl font-bold text-blue-600">
                    {person.name[0]}
                  </div>
                  <h3 className="font-semibold text-gray-900">{person.name}</h3>
                  <p className="text-xs text-blue-600 font-medium mt-0.5">{person.role}</p>
                  <p className="text-sm text-gray-500 mt-2">{person.bio}</p>
                </div>
              ))}
            </div>
          </section>
        </>
      )}

      <section className="bg-blue-600 py-16">
        <div className="max-w-2xl mx-auto text-center px-6">
          <h2 className="text-2xl font-bold text-white mb-4">Want to learn more?</h2>
          <Link to="/contact" className="bg-white text-blue-600 px-8 py-3 rounded-xl font-semibold hover:bg-blue-50">
            Get in Touch
          </Link>
        </div>
      </section>
    </div>
  )
}
