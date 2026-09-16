type FullscreenToggleProps = {
  active: boolean;
  enterLabel: string;
  onToggle: () => void;
  className?: string;
};

export function FullscreenToggle({ active, enterLabel, onToggle, className }: FullscreenToggleProps) {
  const label = active ? "Réduire" : enterLabel;
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
    >
      {label}
    </button>
  );
}
