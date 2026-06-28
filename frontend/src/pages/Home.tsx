import { Link } from "react-router";
import { BracketLegend } from "@/bracket/BracketLegend";

export function Home() {
  return (
    <div className="space-y-6">
      <h1 className="text-4xl font-bold">Welcome to Mundial KO</h1>
      <p className="text-lg text-body-muted">
        Predict the 2026 FIFA World Cup knockout rounds and compete on the
        global leaderboard.
      </p>
      <h2 className="text-3xl">How to Play</h2>
      <div className="flex flex-col gap-5">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-full bg-blue-600 flex items-center justify-center shrink-0">
            <svg
              className="w-6 h-6 text-white"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M4 5h2v4H4zM4 15h2v4H4zM10 7h2v2h-2zM10 15h2v2h-2zM6 7h4M6 17h4M12 8h4M12 16h4M16 8v8M16 12h4"
              />
            </svg>
          </div>
          <p className="text-body-secondary">
            Create a bracket with your predictions for the Knockout Rounds.
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-full bg-blue-600 flex items-center justify-center shrink-0">
            <svg
              className="w-6 h-6 text-white"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
              />
            </svg>
          </div>
          <p className="text-body-secondary">
            Sign up with a Google account to submit your bracket.
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-full bg-blue-600 flex items-center justify-center shrink-0">
            <svg
              className="w-6 h-6 text-white"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
              />
            </svg>
          </div>
          <p className="text-body-secondary">
            Climb the{" "}
            <Link to="/leaderboard" className="text-blue-600 hover:underline">
              Global Leaderboard
            </Link>
            !
          </p>
        </div>
      </div>
      <h2 className="text-3xl">The Point System</h2>
      <p className="text-body-secondary">
        Unlike most bracket prediction games, the goal here isn't necessarily to
        make a perfect bracket. I mean, you should certainly aim to get every
        matchup right, but it is basically impossible.{" "}
        <a
          href="https://www.ncaa.com/news/basketball-men/bracketiq/2026-02-18/perfect-ncaa-bracket-absurd-odds-march-madness-dream"
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 hover:underline"
        >
          The odds of making a perfect NCAA March Madness bracket is 1 in
          9,223,372,036,854,775,808
        </a>
        , and it has never happened since the fan contest started in 1977.
      </p>
      <p className="text-body-secondary">
        Now who likes a game with no winner? Mundial KO uses a point system to
        reward players for the parts of their bracket they get right. There's no
        penalty for getting matchups wrong, but obviously the more right you
        are, the more points you get.
      </p>
      <p className="text-body-secondary">Here's how the point system works:</p>
      <div className="overflow-hidden rounded-xl border border-edge bg-surface shadow-sm">
        <div className="flex items-center gap-2 sm:gap-4 bg-blue-600 px-3 sm:px-4 py-2.5">
          <span className="flex-1 text-xs font-semibold uppercase tracking-wider text-white">
            Round
          </span>
          <span className="w-14 sm:w-20 text-center text-xs font-semibold uppercase tracking-wider text-white">
            Winner
          </span>
          <span className="w-14 sm:w-20 text-center text-xs font-semibold uppercase tracking-wider text-white">
            Score
          </span>
          <span className="w-14 sm:w-20 text-center text-xs font-semibold uppercase tracking-wider text-white">
            PK
          </span>
        </div>
        {[
          {
            round: "Round of 32",
            short: "R32",
            winner: 2,
            score: "—",
            pk: "—",
          },
          {
            round: "Round of 16",
            short: "R16",
            winner: 4,
            score: "—",
            pk: "—",
          },
          {
            round: "Quarter-finals",
            short: "QF",
            winner: 8,
            score: "—",
            pk: "—",
          },
          { round: "Semi-finals", short: "SF", winner: 16, score: 16, pk: 40 },
          { round: "Final", short: "Final", winner: 32, score: 32, pk: 40 },
          { round: "3rd Place", short: "3rd", winner: 10, score: "—", pk: "—" },
        ].map((row, i) => (
          <div
            key={row.round}
            className={`flex items-center gap-2 sm:gap-4 px-3 sm:px-4 py-3 border-b border-edge-light ${
              i % 2 === 0 ? "bg-surface" : "bg-surface-alt"
            }`}
          >
            <span className="flex-1 text-sm font-medium text-body">
              <span className="hidden sm:inline">{row.round}</span>
              <span className="sm:hidden">{row.short}</span>
            </span>
            <span className="w-14 sm:w-20 text-center text-sm font-semibold text-blue-600">
              {row.winner}
            </span>
            <span
              className={`w-14 sm:w-20 text-center text-sm ${row.score === "—" ? "text-body-faint" : "font-semibold text-blue-600"}`}
            >
              {row.score}
            </span>
            <span
              className={`w-14 sm:w-20 text-center text-sm ${row.pk === "—" ? "text-body-faint" : "font-semibold text-blue-600"}`}
            >
              {row.pk}
            </span>
          </div>
        ))}
      </div>
      <p className="text-body-muted">
        Note: The Semi-final and Final matchups require guessing an exact score.
        Points for winner, score (90 + extra time) and penalty kicks are
        rewarded separately. So, there are multiple opportunities to get points
        from these matchups without getting them exactly right.
      </p>
      <h2 className="text-3xl">Your Bracket</h2>
      <p className="text-body-secondary">
        Once you create your bracket, it will be saved to your account and you
        can view its status while logged in. As the knockout rounds progress,
        your bracket will be updated to show you what you're getting right, what
        you're getting wrong, and how many points you're earning.
      </p>
      <p className="text-body-secondary">
        Here's a quick guide on bracket indicators:
      </p>
      <BracketLegend collapsible={false} />
      <h2 className="text-3xl">Late Arrival? No Problem.</h2>
      <p className="text-body-secondary">
        You can still submit a bracket even after the knockout games begin.
        While you won't get any points from games already played by the time of
        your submission, late players get the advantage of more insight into the
        later, more lucrative rounds. If you play your cards right, our point
        system allows you to potentially catch up on the leaderboard and make a
        dramatic underdog run!
      </p>
      <h2 className="text-3xl">General Tips</h2>
      <ul className="text-body-secondary list-disc list-outside space-y-3 ml-6">
        <li>
          While the Round of 32 games don't yield that many points in comparison
          to other rounds, it is still crucial to not get too many of these
          matchups wrong. Too many wrong guesses early on will cascade
          downstream through your bracket and you probably won't see much return
          in later rounds.
        </li>
        <li>
          Football is a game of fine margins, especially in high stakes games
          like the Semi-finals and Final. When making score predictions for
          those games, don't expect the scores or difference in goals to be too
          high. Penalty shootouts usually end with a difference of one or two.
        </li>
      </ul>
      <h2 className="text-3xl">Share With Friends!</h2>
      <p className="text-body-seconday">This game thrives on participation, the more competition the better! Share with your friends and compete to see who's been paying more attention to the World Cup so far!</p>
      <div className="flex flex-col gap-4">
        <a
          href="https://mundialko.com"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 text-blue-600 hover:underline"
        >
          <svg
            className="w-5 h-5 shrink-0"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.658 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
            />
          </svg>
          <strong>www.mundialko.com</strong>
        </a>
        <a
          href="https://github.com/cuhhleed/mundial-ko-world-cup-brackets"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 text-blue-600 hover:underline"
        >
          <svg
            className="w-5 h-5 shrink-0"
            fill="currentColor"
            viewBox="0 0 24 24"
          >
            <path d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.17 6.839 9.49.5.092.682-.217.682-.482 0-.237-.008-.868-.013-1.703-2.782.603-3.369-1.343-3.369-1.343-.454-1.156-1.11-1.463-1.11-1.463-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.544 2.914 1.19.092-.926.35-1.556.636-1.913-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.578 9.578 0 0112 6.836c.85.004 1.705.114 2.504.336 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.578.688.48C19.138 20.167 22 16.418 22 12c0-5.523-4.477-10-10-10z" />
          </svg>
          <strong>cuhhleed/mundial-ko-world-cup-brackets</strong>
        </a>
      </div>
    </div>
  );
}
