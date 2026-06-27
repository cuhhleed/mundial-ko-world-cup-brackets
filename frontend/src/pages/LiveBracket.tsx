import { BracketLayout } from "../bracket/BracketLayout";
import { FEEDERS } from "../bracket/topology";
import { useMatchData, type ApiMatch } from "../bracket/useMatchData";
import type { BracketState, SlotState } from "../bracket/types";

const FIFA_CODE_RE = /^[A-Z]{3}$/;
const GROUP_POS_RE = /^[A-P][12]$/;

function isRealTeam(code: string): boolean {
  return FIFA_CODE_RE.test(code) || GROUP_POS_RE.test(code);
}

function deriveWinner(match: ApiMatch): string | null {
  if (match.pk_winner) return match.pk_winner;
  if (match.home_score !== null && match.away_score !== null) {
    if (match.home_score > match.away_score) return match.home_team;
    if (match.away_score > match.home_score) return match.away_team;
  }
  return null;
}

function resolveTeams(
  match: ApiMatch,
  matches: Record<string, ApiMatch>,
): [string, string] {
  const feeders = FEEDERS[match.match_id];
  if (!feeders) return [match.home_team, match.away_team];

  function resolve(raw: string, feederSlotId: string): string {
    if (isRealTeam(raw)) return raw;
    const feeder = matches[feederSlotId];
    if (feeder?.status === "completed") {
      const winner = deriveWinner(feeder);
      if (winner) return winner;
    }
    return `W${feederSlotId}`;
  }

  return [
    resolve(match.home_team, feeders[0][0]),
    resolve(match.away_team, feeders[1][0]),
  ];
}

function matchToSlotState(
  match: ApiMatch,
  matches: Record<string, ApiMatch>,
): SlotState {
  const hasScores = match.home_score !== null && match.away_score !== null;
  const hasPkScores = match.pk_home_score !== null && match.pk_away_score !== null;
  const teams = resolveTeams(match, matches);

  return {
    slotId: match.match_id,
    teams,
    winner: match.status === "completed" ? deriveWinner(match) : null,
    scores: hasScores ? [match.home_score!, match.away_score!] : null,
    pkScores: hasPkScores ? [match.pk_home_score!, match.pk_away_score!] : null,
    locked: false,
    lockedResult: null,
    status: match.status as SlotState["status"],
    kickoffTime: match.kickoff_time,
  };
}

export function LiveBracket() {
  const { matches, loading, error } = useMatchData();

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="w-8 h-8 border-2 border-edge border-t-blue-500 rounded-full animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <h1 className="text-4xl font-bold">Live Bracket</h1>
        <p className="text-body-muted">{error}</p>
      </div>
    );
  }

  if (!matches) {
    return null;
  }

  const slots: Record<string, SlotState> = {};
  for (const [matchId, match] of Object.entries(matches)) {
    slots[matchId] = matchToSlotState(match, matches);
  }

  const bracketState: BracketState = {
    slots,
    initialSlots: slots,
  };

  return (
    <div className="space-y-6">
      <h1 className="text-4xl font-bold">Live Bracket</h1>
      <BracketLayout bracketState={bracketState} />
    </div>
  );
}
