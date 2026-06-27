import type { TeamRecord } from './useTeamRecords'

export function TeamRecordStack({ wins, draws, losses }: TeamRecord) {
  return (
    <div className="flex flex-row sm:flex-col items-center gap-1 sm:gap-0.5 text-xs font-bold leading-tight sm:w-8">
      <span className="text-win">{wins}W</span>
      <span className="text-body-muted">{draws}D</span>
      <span className="text-loss">{losses}L</span>
    </div>
  )
}
