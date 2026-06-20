import flagSvg from "../../assets/flag.svg";
import type { ApiSlotPrediction } from "./types";

export type SlotCardData = {
  slotId: string;
  teams: [string, string] | null;
  winner: string | null;
  scores: [number, number] | null;
  pkScores: [number, number] | null;
  locked: boolean;
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
  isCorrect,
}: {
  name: string;
  score: number | null;
  isWinner: boolean;
  isCorrect?: boolean;
}) {
  return (
    <div
      className={[
        "flex items-center justify-between px-2 py-1 rounded text-xs",
        isWinner ? "bg-blue-50 font-bold text-blue-900" : "text-gray-600",
      ].join(" ")}
    >
      <span className="flex items-center gap-1 truncate max-w-24">
        <img src={flagSvg} alt="" className="w-3.5 h-3.5 shrink-0" />
        <span className="truncate">{name}</span>
      </span>
      <div className="flex items-center gap-1 ml-1">
        {score !== null && (
          <span className={isWinner ? "text-blue-700" : "text-gray-400"}>
            {score}
          </span>
        )}
        {isCorrect !== undefined && <span>{isCorrect ? "✓" : "✗"}</span>}
      </div>
    </div>
  );
}

export function BracketSlotCard({ slot, viewer }: Props) {
  const { teams, winner, scores, pkScores, locked } = slot;

  const team1 = teams?.[0] ?? "TBD";
  const team2 = teams?.[1] ?? "TBD";

  const correctWinner = viewer ? winner === viewer.result.winner : undefined;

  return (
    <div
      className={[
        "w-full rounded-lg border bg-white shadow-sm text-[11px] overflow-hidden",
        locked ? "border-amber-300 bg-amber-50/50" : "border-gray-200",
        viewer && correctWinner ? "border-green-400" : "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {/* Lock icon + teams row */}
      <div className="flex">
        {locked && (
          <div className="flex items-center justify-center w-5 shrink-0 bg-amber-100 text-amber-600">
            <svg viewBox="0 0 20 20" fill="currentColor" className="w-3 h-3">
              <path fillRule="evenodd" d="M10 1a4.5 4.5 0 00-4.5 4.5V9H5a2 2 0 00-2 2v6a2 2 0 002 2h10a2 2 0 002-2v-6a2 2 0 00-2-2h-.5V5.5A4.5 4.5 0 0010 1zm3 8V5.5a3 3 0 10-6 0V9h6z" clipRule="evenodd" />
            </svg>
          </div>
        )}
        <div className="flex-1 flex flex-col divide-y divide-gray-100">
          <TeamRow
            name={team1}
            score={scores?.[0] ?? null}
            isWinner={winner === team1}
            isCorrect={
              viewer
                ? viewer.result.winner === team1 && winner === team1
                : undefined
            }
          />
          <TeamRow
            name={team2}
            score={scores?.[1] ?? null}
            isWinner={winner === team2}
            isCorrect={
              viewer
                ? viewer.result.winner === team2 && winner === team2
                : undefined
            }
          />
        </div>
      </div>

      {/* PK row */}
      {pkScores && (
        <div className="flex justify-between px-2 py-0.5 bg-amber-50 border-t border-amber-100 text-[10px] text-amber-700">
          <span>PK</span>
          <span>
            {pkScores[0]} – {pkScores[1]}
          </span>
        </div>
      )}

      {/* Viewer extras: points badge */}
      {viewer && viewer.points !== null && (
        <div className="px-2 py-0.5 bg-green-50 border-t border-green-100 text-[10px] text-green-700 font-semibold text-right">
          +{viewer.points} pts
        </div>
      )}
    </div>
  );
}
