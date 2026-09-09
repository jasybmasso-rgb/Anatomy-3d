import { useEffect, useId, useMemo, useRef, useState, type KeyboardEvent } from "react";
import type { Muscle } from "../types/muscle";
import { searchMuscles } from "../lib/searchMuscles";

type SearchBarProps = {
  muscles: Muscle[];
  selectedId: string | null;
  resetToken: number;
  onSelect: (id: string) => void;
};

export function SearchBar({ muscles, selectedId, resetToken, onSelect }: SearchBarProps) {
  const listId = useId();
  const inputRef = useRef<HTMLInputElement>(null);
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);

  useEffect(() => {
    setQuery("");
    setOpen(false);
    setActive(0);
  }, [resetToken]);

  const results = useMemo(() => searchMuscles(muscles, query).slice(0, 8), [muscles, query]);

  useEffect(() => {
    setActive(0);
  }, [query]);

  function choose(muscle: Muscle) {
    onSelect(muscle.id);
    setQuery(muscle.name);
    setOpen(false);
  }

  function onKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setOpen(true);
      setActive((i) => Math.min(i + 1, Math.max(0, results.length - 1)));
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActive((i) => Math.max(i - 1, 0));
    } else if (event.key === "Enter") {
      if (open && results[active]) {
        event.preventDefault();
        choose(results[active]);
      }
    } else if (event.key === "Escape") {
      setOpen(false);
    }
  }

  return (
    <div className="search">
      <label className="search-label" htmlFor="muscle-search">
        Recherche
      </label>
      <input
        ref={inputRef}
        id="muscle-search"
        className="search-input"
        type="search"
        role="combobox"
        placeholder="Rechercher un muscle…"
        autoComplete="off"
        aria-autocomplete="list"
        aria-expanded={open && results.length > 0}
        aria-controls={listId}
        aria-activedescendant={open && results[active] ? `${listId}-${results[active].id}` : undefined}
        value={query}
        onChange={(event) => {
          setQuery(event.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        onKeyDown={onKeyDown}
        onBlur={() => {
          window.setTimeout(() => setOpen(false), 120);
        }}
      />
      {open && results.length > 0 ? (
        <ul id={listId} className="search-list" role="listbox">
          {results.map((muscle, index) => (
            <li key={muscle.id} role="presentation">
              <button
                type="button"
                id={`${listId}-${muscle.id}`}
                role="option"
                aria-selected={muscle.id === selectedId || index === active}
                className={
                  index === active ? "search-option search-option-active" : "search-option"
                }
                onMouseDown={(event) => {
                  event.preventDefault();
                  choose(muscle);
                }}
              >
                <span className="search-option-name">{muscle.name}</span>
                <span className="search-option-latin">{muscle.nameLatin}</span>
              </button>
            </li>
          ))}
        </ul>
      ) : null}
      {open && query.trim() && results.length === 0 ? (
        <p className="search-empty" role="status">
          Aucun muscle ne correspond à « {query} ».
        </p>
      ) : null}
    </div>
  );
}
