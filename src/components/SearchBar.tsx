import { useEffect, useId, useMemo, useRef, useState, type KeyboardEvent } from "react";
import type { Muscle } from "../types/muscle";
import type { ConnectivePart, StructureKind, VisceraPart } from "../types/structure";
import { STRUCTURE_KIND_LABEL } from "../types/structure";
import { searchStructures, type SearchHit } from "../lib/searchStructures";

type SearchBarProps = {
  muscles: Muscle[];
  viscera: VisceraPart[];
  connective: ConnectivePart[];
  selectedId: string | null;
  selectedKind: StructureKind | null;
  resetToken: number;
  onSelect: (kind: StructureKind, id: string) => void;
};

export function SearchBar({
  muscles,
  viscera,
  connective,
  selectedId,
  selectedKind,
  resetToken,
  onSelect,
}: SearchBarProps) {
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

  const results = useMemo(
    () => searchStructures(muscles, viscera, connective, query).slice(0, 12),
    [muscles, viscera, connective, query],
  );

  useEffect(() => {
    setActive(0);
  }, [query]);

  function choose(hit: SearchHit) {
    onSelect(hit.kind, hit.id);
    setQuery(hit.name);
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
      <label className="search-label" htmlFor="structure-search">
        Recherche
      </label>
      <input
        ref={inputRef}
        id="structure-search"
        className="search-input"
        type="search"
        role="combobox"
        placeholder="Rechercher un muscle, un ligament, un nerf…"
        autoComplete="off"
        aria-autocomplete="list"
        aria-expanded={open && results.length > 0}
        aria-controls={listId}
        aria-activedescendant={
          open && results[active] ? `${listId}-${results[active].kind}-${results[active].id}` : undefined
        }
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
          {results.map((hit, index) => (
            <li key={`${hit.kind}-${hit.id}`} role="presentation">
              <button
                type="button"
                id={`${listId}-${hit.kind}-${hit.id}`}
                role="option"
                aria-selected={
                  (hit.kind === selectedKind && hit.id === selectedId) || index === active
                }
                className={index === active ? "search-option search-option-active" : "search-option"}
                onMouseDown={(event) => {
                  event.preventDefault();
                  choose(hit);
                }}
              >
                <span className="search-option-name">
                  {hit.name}
                  <em className="search-option-kind">{STRUCTURE_KIND_LABEL[hit.kind]}</em>
                </span>
                <span className="search-option-latin">{hit.nameLatin}</span>
              </button>
            </li>
          ))}
        </ul>
      ) : null}
      {open && query.trim() && results.length === 0 ? (
        <p className="search-empty" role="status">
          Aucune structure ne correspond à « {query} ».
        </p>
      ) : null}
    </div>
  );
}
