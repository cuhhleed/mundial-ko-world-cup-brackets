import { useState } from "react";
import fallbackSvg from "../../assets/flag.svg";

type Props = {
  code: string;
  className?: string;
};

export function TeamFlag({ code, className = "" }: Props) {
  const [useFallback, setUseFallback] = useState(false);

  const src =
    !code || code === "TBD" || useFallback
      ? fallbackSvg
      : `/flags/${code}.svg`;

  return (
    <img
      src={src}
      alt={code}
      className={`select-none ${className}`}
      onError={() => setUseFallback(true)}
    />
  );
}
