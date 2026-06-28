import { TeamFlag } from '../components/TeamFlag'
import { TeamRecordStack } from './TeamRecordStack'
import type { TeamRecord } from './useTeamRecords'

type Props = {
  slotId: string
  teams: [string, string] | null
  records: Record<string, TeamRecord> | null
  onSelect: (winner: string) => void
  selectedTeam?: string | null
}

function slotLabel(slotId: string): string {
  if (slotId.startsWith('R32-')) return `Round of 32 — Match ${slotId.slice(4)}`
  if (slotId.startsWith('R16-')) return `Round of 16 — Match ${slotId.slice(4)}`
  if (slotId.startsWith('QF-')) return `Quarter-final ${slotId.slice(3)}`
  if (slotId === 'TP') return 'Third Place'
  return slotId
}

export function WizardPrompt({ slotId, teams, records, onSelect, selectedTeam = null }: Props) {
  if (!teams) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-16 text-body-faint">
        <span className="text-4xl">⏳</span>
        <p className="text-lg">{slotLabel(slotId)}</p>
        <p className="text-sm">Waiting for upstream picks…</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col items-center gap-8 py-8">
      <h2 className="text-base font-medium text-body-muted tracking-wide uppercase">
        {slotLabel(slotId)}
      </h2>
      <p className="text-xl font-semibold text-body-secondary">
        {slotId === 'FINAL'
          ? 'Who is the 2026 World Cup Champion?'
          : slotId === 'TP'
          ? 'Who takes bronze?'
          : 'Who advances?'}
      </p>
      <div className="flex flex-col items-center gap-4">
        <div className="flex items-center gap-3">
          {records?.[teams[0]] && <div className="hidden sm:block"><TeamRecordStack {...records[teams[0]]} /></div>}
          {teams.map((team) => (
            <button
              key={team}
              type="button"
              onClick={() => onSelect(team)}
              disabled={!!selectedTeam}
              className={`group flex flex-col items-center gap-4 px-8 py-6 rounded-2xl border-2
                         bg-surface focus:outline-none
                         transition-all duration-300 w-44
                         ${selectedTeam === team
                           ? 'border-blue-500 bg-blue-50 scale-105 shadow-md'
                           : selectedTeam
                             ? 'border-edge opacity-30 scale-95'
                             : 'border-edge hover:border-blue-500 hover:bg-blue-50 hover:shadow-md focus:border-blue-500 active:scale-95 cursor-pointer'
                         }`}
            >
              <TeamFlag code={team} className="w-16 h-16" />
              <span className="text-lg font-bold text-body group-hover:text-blue-600 text-center leading-tight transition-colors">{team}</span>
            </button>
          ))}
          {records?.[teams[1]] && <div className="hidden sm:block"><TeamRecordStack {...records[teams[1]]} /></div>}
        </div>
        {records && (records[teams[0]] || records[teams[1]]) && (
          <div className="flex justify-center gap-3 sm:hidden">
            <div className="w-44 flex justify-center">
              {records[teams[0]] && <TeamRecordStack {...records[teams[0]]} />}
            </div>
            <div className="w-44 flex justify-center">
              {records[teams[1]] && <TeamRecordStack {...records[teams[1]]} />}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
