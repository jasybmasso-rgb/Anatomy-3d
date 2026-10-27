type FullscreenToggleProps = {
  active: boolean;
  onToggle: () => void;
  className?: string;
};

const ENTER_LABEL = "Plein écran";
const EXIT_LABEL = "Quitter le plein écran";

function ExpandIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      <path
        d="M9 4H4v5M15 4h5v5M20 15v5h-5M4 15v5h5"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function CollapseIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      <path
        d="M4 9h5V4M20 9h-5V4M15 20v-5h5M9 20v-5H4"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function FullscreenToggle({ active, onToggle, className }: FullscreenToggleProps) {
  const label = active ? EXIT_LABEL : ENTER_LABEL;
  return (
    <button
      type="button"
      className={`fs-btn${active ? " fs-btn-exit" : ""}${className ? ` ${className}` : ""}`}
      onClick={(event) => {
        event.stopPropagation();
        onToggle();
      }}
      aria-pressed={active}
      aria-label={label}
      title={label}
    >
      {active ? <CollapseIcon /> : <ExpandIcon />}
    </button>
  );
}
