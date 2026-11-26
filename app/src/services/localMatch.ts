import catalog from "../domain/precedentCatalog.json";
import { ranked } from "../domain/matchPrecedent";
import type { Precedent } from "../domain/model";

export function localMatch(category: string, description: string): Precedent[] {
  if (!Object.prototype.hasOwnProperty.call(catalog, category)) return [];
  const hits = ranked(description, catalog[category as keyof typeof catalog]).slice(0, 3);
  return hits.map(hit => ({
    id: hit.id, title: hit.title, caseNumber: hit.number, court: hit.court,
    judgmentDate: hit.date, summary: hit.summary, sourceUrl: hit.sourceUrl,
  }));
}
