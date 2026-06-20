import flagSvg from '../../assets/flag.svg'

type Props = {
  slotId: string
  teams: [string, string] | null
  onSelect: (winner: string) => void
}

function slotLabel(slotId: string): string {
  if (slotId.startsWith('R32-')) return `Round of 32 — Match ${slotId.slice(4)}`
  if (slotId.startsWith('R16-')) return `Round of 16 — Match ${slotId.slice(4)}`
  if (slotId.startsWith('QF-')) return `Quarter-final ${slotId.slice(3)}`
  if (slotId === 'TP') return 'Third Place'
  return slotId
}

export function WizardPrompt({ slotId, teams, onSelect }: Props) {
  if (!teams) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-16 text-gray-400">
        <span className="text-4xl">⏳</span>
        <p className="text-lg">{slotLabel(slotId)}</p>
        <p className="text-sm">Waiting for upstream picks…</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col items-center gap-8 py-8">
      <h2 className="text-base font-medium text-gray-500 tracking-wide uppercase">
        {slotLabel(slotId)}
      </h2>
      <p className="text-xl font-semibold text-gray-700">Who advances?</p>
      <div className="flex gap-6">
        {teams.map((team) => (
          <button
            key={team}
            type="button"
            onClick={() => onSelect(team)}
            className="flex flex-col items-center gap-4 px-8 py-6 rounded-2xl border-2 border-gray-200
                       bg-white hover:border-blue-500 hover:bg-blue-50 hover:shadow-md
                       focus:outline-none focus:border-blue-500
                       active:scale-95 transition-all duration-100 w-44 cursor-pointer"
          >
            <img src={flagSvg} alt="" className="w-16 h-16 select-none" />
            <span className="text-lg font-bold text-gray-800 text-center leading-tight">{team}</span>
          </button>
        ))}
      </div>
    </div>
  )
}
