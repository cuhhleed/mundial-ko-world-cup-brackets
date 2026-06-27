import { Fragment } from "react";
import { BracketSlotCard, type SlotCardData } from "./BracketSlotCard";
import type { ApiSlotPrediction } from "./types";

// Layout constants (shared with BracketLayout)
export const UNIT = 64; // px per R32 bracket unit
export const CARD_H = 48; // px — accounts for locked banner / PK row
export const CONN_W = 28; // px — width of connector arm area to the right

type ViewerExtrasMap = Record<
  string,
  { result: ApiSlotPrediction; points: number | null }
>;

type Props = {
  roundIndex: number; // 0=R32, 1=R16, 2=QF, 3=SF
  label: string;
  slots: SlotCardData[];
  showConnectors?: boolean;
  viewerExtras?: ViewerExtrasMap;
};

export function RoundColumn({
  roundIndex,
  label,
  slots,
  showConnectors = true,
  viewerExtras,
}: Props) {
  const span = Math.pow(2, roundIndex); // units per slot: 1, 2, 4, 8
  const totalHeight = 16 * UNIT; // 1024px
  const colWidth = 160; // card column width

  const pairs = Math.floor(slots.length / 2);

  return (
    <div
      className="flex flex-col"
      style={{ minWidth: colWidth + (showConnectors ? CONN_W : 0) }}
    >
      {/* Round label */}
      <div
        className="text-xs font-semibold text-body-faint uppercase tracking-wider text-center pb-2"
        style={{ width: colWidth }}
      >
        {label}
      </div>

      {/* Bracket column */}
      <div
        className="relative flex-1"
        style={{
          height: totalHeight,
          width: colWidth + (showConnectors ? CONN_W : 0),
        }}
      >
        {/* Slot cards */}
        {slots.map((slot, i) => {
          const cardCenterY = (i * span + span / 2) * UNIT;
          const cardTopY = cardCenterY - CARD_H / 2;

          return (
            <div
              key={slot.slotId}
              className="absolute"
              style={{
                top: cardTopY,
                left: 0,
                width: colWidth,
              }}
            >
              <BracketSlotCard
                slot={slot}
                viewer={viewerExtras?.[slot.slotId]}
              />
            </div>
          );
        })}

        {/* Connector lines (right side) */}
        {showConnectors &&
          Array.from({ length: pairs }, (_, k) => {
            const topCenterY = (2 * k * span + span / 2) * UNIT;
            const bottomCenterY = ((2 * k + 1) * span + span / 2) * UNIT;
            const midY = (2 * k + 1) * span * UNIT;

            return (
              <Fragment key={k}>
                {/* Horizontal arm — top feeder */}
                <div
                  className="absolute bg-connector"
                  style={{
                    top: topCenterY - 1,
                    left: colWidth,
                    width: CONN_W / 2,
                    height: 2,
                  }}
                />
                {/* Horizontal arm — bottom feeder */}
                <div
                  className="absolute bg-connector"
                  style={{
                    top: bottomCenterY - 1,
                    left: colWidth,
                    width: CONN_W / 2,
                    height: 2,
                  }}
                />
                {/* Vertical bar joining the two arms */}
                <div
                  className="absolute bg-connector"
                  style={{
                    top: topCenterY,
                    left: colWidth + CONN_W / 2 - 1,
                    width: 2,
                    height: bottomCenterY - topCenterY,
                  }}
                />
                {/* Horizontal arm from midpoint → next column */}
                <div
                  className="absolute bg-connector"
                  style={{
                    top: midY - 1,
                    left: colWidth + CONN_W / 2,
                    width: CONN_W / 2,
                    height: 2,
                  }}
                />
              </Fragment>
            );
          })}
      </div>
    </div>
  );
}
