import { BarChart3, Bell, Home, Map } from 'lucide-react'
import { NavLink, Outlet } from 'react-router-dom'

const ITEMS = [
  { to: '/', label: 'Início', icon: Home },
  { to: '/mapa', label: 'Mapa', icon: Map },
  { to: '/comparar', label: 'Comparar', icon: BarChart3 },
  { to: '/alertas', label: 'Alertas', icon: Bell },
]

const focusRing =
  'focus-visible:outline-3 focus-visible:outline-offset-2 focus-visible:outline-blue-600'

const linkClass = ({ isActive }: { isActive: boolean }) =>
  `flex min-h-11 items-center gap-3 rounded-xl px-3 font-medium transition-colors ${focusRing} ${
    isActive ? 'bg-neutral-900 text-white' : 'text-neutral-700 hover:bg-neutral-200'
  }`

const tabClass = ({ isActive }: { isActive: boolean }) =>
  `flex min-h-14 flex-1 flex-col items-center justify-center gap-0.5 text-xs font-medium ${focusRing} ${
    isActive ? 'text-neutral-900' : 'text-neutral-500'
  }`

export function Layout({ footer }: { footer?: React.ReactNode }) {
  return (
    <div className="min-h-dvh bg-neutral-50 text-neutral-900 md:flex">
      <a
        href="#conteudo"
        className="sr-only z-50 rounded-lg bg-white p-3 focus:not-sr-only focus:fixed focus:top-2 focus:left-2"
      >
        Pular para o conteúdo
      </a>

      <aside className="sticky top-0 hidden h-dvh w-60 shrink-0 border-r border-neutral-200 bg-white p-4 md:block">
        <p className="mb-6 px-3 text-lg font-bold tracking-tight">Monitor UV</p>
        <nav aria-label="Principal">
          <ul className="flex flex-col gap-1">
            {ITEMS.map(({ to, label, icon: Icon }) => (
              <li key={to}>
                <NavLink to={to} end={to === '/'} className={linkClass}>
                  <Icon aria-hidden="true" size={20} /> {label}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <main
          id="conteudo"
          tabIndex={-1}
          className="mx-auto w-full max-w-5xl flex-1 p-4 pb-6 outline-none md:p-8"
        >
          <Outlet />
        </main>
        {footer}
      </div>

      <nav
        aria-label="Principal (móvel)"
        className="fixed inset-x-0 bottom-0 z-[1000] border-t border-neutral-200 bg-white pb-[env(safe-area-inset-bottom)] md:hidden"
      >
        <ul className="flex">
          {ITEMS.map(({ to, label, icon: Icon }) => (
            <li key={to} className="flex flex-1">
              <NavLink to={to} end={to === '/'} className={tabClass}>
                <Icon aria-hidden="true" size={22} />
                {label}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
    </div>
  )
}
