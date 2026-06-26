import { useEffect, useRef, useState } from "react";
import { api } from "@/api/client";

export type ApiMatch = {
  match_id: string;
  round: string;
  match_number: number;
  home_team: string;
  away_team: string;
  home_score: number | null;
  away_score: number | null;
  pk_home_score: number | null;
  pk_away_score: number | null;
  pk_winner: string | null;
  status: string;
  kickoff_time: string;
};

type MatchesByRoundResponse = {
  rounds: Record<string, ApiMatch[]>;
};

type UseMatchDataResult = {
  matches: Record<string, ApiMatch> | null;
  loading: boolean;
  error: string | null;
};

const POLL_INTERVAL_MS = 30_000;

export function useMatchData(): UseMatchDataResult {
  const [matches, setMatches] = useState<Record<string, ApiMatch> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const cancelledRef = useRef(false);

  useEffect(() => {
    cancelledRef.current = false;

    async function fetchMatches() {
      try {
        const data = await api.get<MatchesByRoundResponse>("/api/matches");
        if (cancelledRef.current) return;

        // Flatten by-round response into a flat match_id → ApiMatch dict
        const flat: Record<string, ApiMatch> = {};
        for (const roundMatches of Object.values(data.rounds)) {
          for (const match of roundMatches) {
            flat[match.match_id] = match;
          }
        }

        setMatches(flat);
        setError(null);
      } catch (err) {
        if (cancelledRef.current) return;
        setError(err instanceof Error ? err.message : "Failed to load matches.");
      } finally {
        if (!cancelledRef.current) setLoading(false);
      }
    }

    fetchMatches();

    const intervalId = setInterval(fetchMatches, POLL_INTERVAL_MS);

    return () => {
      cancelledRef.current = true;
      clearInterval(intervalId);
    };
  }, []);

  return { matches, loading, error };
}
