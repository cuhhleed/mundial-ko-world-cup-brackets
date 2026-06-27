import { useState } from "react";

function LegendItem({ icon, label }: { icon: React.ReactNode; label: string }) {
  return (
    <div className="flex items-center gap-2">
      <div className="flex items-center justify-center w-5 h-5 shrink-0">
        {icon}
      </div>
      <span>{label}</span>
    </div>
  );
}

export function BracketLegend({
  collapsible = true,
}: {
  collapsible?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const show = !collapsible || open;

  return (
    <div className="rounded-xl border border-edge bg-surface shadow-sm text-sm">
      {collapsible ? (
        <button
          type="button"
          onClick={() => setOpen(!open)}
          className="flex items-center justify-between w-full px-5 py-3 text-left cursor-pointer"
        >
          <span className="font-semibold text-body-secondary">
            Bracket Guide
          </span>
          <svg
            className={`w-4 h-4 text-body-faint transition-transform ${open ? "rotate-180" : ""}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </button>
      ) : null}

      {show && (
        <div
          className={`px-5 pb-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-x-8 gap-y-2 text-xs text-body-muted ${collapsible ? "border-t border-edge-light" : ""} pt-3`}
        >
          <p className="font-semibold text-body-secondary sm:col-span-2 lg:col-span-3 mb-1">
            Side Banners
          </p>
          <LegendItem
            icon={
              <div className="w-4 h-5 rounded-sm bg-green-100 flex items-center justify-center">
                <svg
                  viewBox="0 0 20 20"
                  fill="currentColor"
                  className="w-3 h-3 text-green-600"
                >
                  <path
                    fillRule="evenodd"
                    d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
            }
            label="You predicted the correct winner"
          />
          <LegendItem
            icon={
              <div className="w-4 h-5 rounded-sm bg-red-50 flex items-center justify-center">
                <svg
                  viewBox="0 0 20 20"
                  fill="currentColor"
                  className="w-3 h-3 text-red-400"
                >
                  <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
                </svg>
              </div>
            }
            label="You predicted the wrong winner"
          />
          <LegendItem
            icon={
              <div className="w-4 h-5 rounded-sm bg-amber-100 flex items-center justify-center">
                <svg
                  viewBox="0 0 20 20"
                  fill="currentColor"
                  className="w-3 h-3 text-amber-600"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 1a4.5 4.5 0 00-4.5 4.5V9H5a2 2 0 00-2 2v6a2 2 0 002 2h10a2 2 0 002-2v-6a2 2 0 00-2-2h-.5V5.5A4.5 4.5 0 0010 1zm3 8V5.5a3 3 0 10-6 0V9h6z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
            }
            label="Match was already decided when you created your bracket"
          />

          <p className="font-semibold text-body-secondary sm:col-span-2 lg:col-span-3 mt-2 mb-1">
            Icons
          </p>
          <LegendItem
            icon={
              <svg
                viewBox="0 0 20 20"
                fill="currentColor"
                className="w-4 h-4 text-green-600"
              >
                <path
                  fillRule="evenodd"
                  d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z"
                  clipRule="evenodd"
                />
              </svg>
            }
            label="Correct winner prediction"
          />
          <LegendItem
            icon={
              <svg
                viewBox="0 0 20 20"
                fill="currentColor"
                className="w-4 h-4 text-red-400"
              >
                <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
              </svg>
            }
            label="Incorrect winner prediction"
          />
          <LegendItem
            icon={
              <svg
                viewBox="0 0 20 20"
                fill="currentColor"
                className="w-4 h-4 text-green-600"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm0-2a6 6 0 100-12 6 6 0 000 12zm0-2a4 4 0 100-8 4 4 0 000 8zm0-2a2 2 0 100-4 2 2 0 000 4z"
                  clipRule="evenodd"
                />
              </svg>
            }
            label="Bullseye — you nailed the exact score"
          />

          <p className="font-semibold text-body-secondary sm:col-span-2 lg:col-span-3 mt-2 mb-1">
            Other
          </p>
          <LegendItem
            icon={
              <span className="w-2 h-2 rounded-full bg-red-500 animate-[blink_1.4s_infinite]" />
            }
            label="Match is currently live"
          />
          <LegendItem
            icon={
              <div className="w-4 h-5 rounded-sm bg-blue-600 flex items-center justify-center text-[7px] font-semibold text-white leading-none">
                6/28
              </div>
            }
            label="Scheduled kickoff date"
          />
          <LegendItem
            icon={
              <span className="text-[9px] font-bold text-green-600">+3</span>
            }
            label="Points earned from a match"
          />
        </div>
      )}
    </div>
  );
}
