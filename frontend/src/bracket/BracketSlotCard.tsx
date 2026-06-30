import { TeamFlag } from "../components/TeamFlag";
import type { ApiSlotPrediction } from "./types";

export type SlotCardData = {
  slotId: string;
  teams: [string, string] | null;
  winner: string | null;
  scores: [number, number] | null;
  pkScores: [number, number] | null;
  locked: boolean;
  status?: "scheduled" | "live" | "completed";
  kickoffTime?: string;
};

type ViewerExtras = {
  result: ApiSlotPrediction;
  points: number | null;
};

type Props = {
  slot: SlotCardData;
  // When provided, renders accuracy indicators (viewer mode)
  viewer?: ViewerExtras;
};

function TeamRow({
  name,
  score,
  isWinner,
}: {
  name: string;
  score: number | null;
  isWinner: boolean;
}) {
  return (
    <div
      className={[
        "flex items-center justify-between px-2 py-1 rounded text-xs",
        isWinner ? "bg-surface-alt font-bold text-body" : "text-body-muted",
      ].join(" ")}
    >
      <span className="flex items-center gap-1 truncate max-w-24">
        <TeamFlag code={name} className="w-3.5 h-3.5 shrink-0" />
        <span className="truncate">{name}</span>
      </span>
      {score !== null && (
        <span className={isWinner ? "text-blue-700" : "text-body-faint"}>
          {score}
        </span>
      )}
    </div>
  );
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  return `${d.getMonth() + 1}/${d.getDate()}`;
}

export function BracketSlotCard({ slot, viewer }: Props) {
  const { teams, winner, scores, pkScores, locked, status, kickoffTime } = slot;

  const team1 = teams?.[0] ?? "TBD";
  const team2 = teams?.[1] ?? "TBD";

  const winnerCorrect = viewer ? winner === viewer.result.winner : undefined;
  const scoreCorrect =
    viewer && scores && viewer.result.scores && teams
      ? viewer.result.scores[teams[0]] === scores[0] &&
        viewer.result.scores[teams[1]] === scores[1]
      : false;

  const showAccuracyBanner = viewer && winnerCorrect !== undefined;

  return (
    <div
      className={[
        "w-full rounded-lg border bg-surface shadow-sm text-[11px] overflow-hidden",
        locked ? "border-amber-300 bg-amber-50/50" : "border-edge",
        showAccuracyBanner && winnerCorrect ? "border-green-400" : "",
        showAccuracyBanner && !winnerCorrect ? "border-red-300" : "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {/* Lock icon / accuracy banner + teams row */}
      <div className="flex">
        {locked && !showAccuracyBanner && (
          <div className="flex items-center justify-center w-5 shrink-0 bg-amber-100 text-amber-600">
            <svg viewBox="0 0 20 20" fill="currentColor" className="w-3 h-3">
              <path fillRule="evenodd" d="M10 1a4.5 4.5 0 00-4.5 4.5V9H5a2 2 0 00-2 2v6a2 2 0 002 2h10a2 2 0 002-2v-6a2 2 0 00-2-2h-.5V5.5A4.5 4.5 0 0010 1zm3 8V5.5a3 3 0 10-6 0V9h6z" clipRule="evenodd" />
            </svg>
          </div>
        )}
        {!locked && !showAccuracyBanner && status === "live" && (
          <div className="flex items-center justify-center w-5 shrink-0 bg-red-50">
            <span className="w-2 h-2 rounded-full bg-red-500 animate-[blink_1.4s_infinite]" />
          </div>
        )}
        {!locked && !showAccuracyBanner && status !== "live" && kickoffTime && (
          <div className="flex items-center justify-center w-5 shrink-0 bg-blue-600 text-[8px] font-semibold text-white leading-tight">
            {formatDate(kickoffTime)}
          </div>
        )}
        {showAccuracyBanner && (
          <div
            className={[
              "flex flex-col items-center justify-center w-5 shrink-0 gap-0.5",
              winnerCorrect
                ? "bg-green-100 text-green-600"
                : "bg-red-50 text-red-400",
            ].join(" ")}
          >
            {/* Checkmark = correct winner */}
            {winnerCorrect && (
              <svg viewBox="0 0 20 20" fill="currentColor" className="w-3 h-3">
                <path fillRule="evenodd" d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z" clipRule="evenodd" />
              </svg>
            )}
            {/* X = incorrect winner */}
            {!winnerCorrect && (
              <svg viewBox="0 0 20 20" fill="currentColor" className="w-3 h-3">
                <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
              </svg>
            )}
            {/* Bullseye = correct score */}
            {winnerCorrect && scoreCorrect && (
              <svg viewBox="0 0 20 20" fill="currentColor" className="w-3 h-3">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm0-2a6 6 0 100-12 6 6 0 000 12zm0-2a4 4 0 100-8 4 4 0 000 8zm0-2a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
              </svg>
            )}
            {viewer.points !== null && viewer.points > 0 && (
              <span className="text-[9px] font-bold leading-none">
                +{viewer.points}
              </span>
            )}
          </div>
        )}
        <div className="flex-1 flex flex-col divide-y divide-edge-light">
          <TeamRow
            name={team1}
            score={scores?.[0] ?? null}
            isWinner={winner === team1}
          />
          <TeamRow
            name={team2}
            score={scores?.[1] ?? null}
            isWinner={winner === team2}
          />
        </div>
        {pkScores && (
          <div className="flex flex-col items-center justify-center w-5 shrink-0 bg-amber-50 text-[10px] font-semibold text-amber-700 divide-y divide-amber-200">
            <span className="flex-1 flex items-center">{pkScores[0]}</span>
            <span className="flex-1 flex items-center">{pkScores[1]}</span>
          </div>
        )}
      </div>

    </div>
  );
}
