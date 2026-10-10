import { NavLink, Outlet } from 'react-router-dom'
import { getHealth, USE_MOCKS } from '../services/api'
import { useAsync } from '../hooks/useAsync'
import { OfflineBanner } from './StatusStates'

const navClass = ({ isActive }: { isActive: boolean }) =>
  `rounded-md px-3.5 py-2.5 no-underline ${isActive ? 'bg-white/15 font-semibold text-white' : 'text-[#d3dde8] hover:text-white'}`

function ApiIndicator() {
  const health = useAsync(getHealth)
  let dot = '#e8a33d'
  let text = 'Mock data mode · API not connected'
  if (!USE_MOCKS) {
    if (health.loading && !health.data) {
      dot = '#9aa7b6'
      text = 'Checking API…'
    } else if (health.data?.status === 'ok') {
      dot = '#5fd08a'
      text = 'API connected'
    } else {
      dot = '#ff7a59'
      text = 'API unreachable'
    }
  }
  return (
    <div className="flex items-center gap-2 text-[13px] text-[#d3dde8] sm:ml-auto">
      <span className="h-2 w-2 rounded-full" style={{ background: dot }} aria-hidden="true" />
      {text}
    </div>
  )
}

export default function Layout() {
  return (
    <div className="min-h-screen">
      <header className="bg-ink text-white">
        <div className="mx-auto flex max-w-[1360px] flex-wrap items-center gap-x-8 gap-y-3 px-4 py-3 sm:px-6">
          <NavLink to="/" className="flex items-center gap-2.5 text-white no-underline">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#7FB3F0" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M12 3s6 6.5 6 11a6 6 0 0 1-12 0c0-4.5 6-11 6-11z" />
              <path d="M9 15a3 3 0 0 0 3 3" />
            </svg>
            <span className="text-[19px] font-bold">FloodGuard</span>
            <span className="text-[13px] text-[#b9c6d6]">Mumbai</span>
          </NavLink>
          <nav aria-label="Main" className="flex flex-wrap gap-1">
            <NavLink to="/" end className={navClass}>Map</NavLink>
            <NavLink to="/report" className={navClass}>Report flooding</NavLink>
            <NavLink to="/responder" className={navClass}>Responder</NavLink>
          </nav>
          <ApiIndicator />
        </div>
      </header>
      <OfflineBanner />
      <div className="border-b border-warn-line bg-warn-bg">
        <p className="mx-auto m-0 max-w-[1360px] px-4 py-2.5 text-sm text-warn-ink sm:px-6">
          <strong>Prototype decision support.</strong> Scores are heuristic estimates, not flood predictions or official
          warnings. Follow BMC and IMD advisories.
        </p>
      </div>
      <Outlet />
    </div>
  )
}
