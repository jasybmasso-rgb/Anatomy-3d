/** Retire les diacritiques pour une recherche insensible aux accents (fr-CA). */
export function stripAccents(value: string): string {
  return value.normalize("NFD").replace(/\p{M}/gu, "");
}

export function normalizeSearch(value: string): string {
  return stripAccents(value)
    .toLocaleLowerCase("fr-CA")
    .replace(/[-'’]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}
