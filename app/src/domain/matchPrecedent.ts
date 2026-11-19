// Character fragments allow partial matches across Korean particles and verb endings.
const synonyms: [RegExp, string][] = [
  [/핸드폰|휴대폰|휴대전화/g, "스마트폰"],
  [/윗집|윗층/g, "위층"], [/아랫집|아랫층/g, "아래층"],
  [/발망치|쿵쿵|발소리/g, "층간소음"], [/비행기/g, "항공기"],
  [/월급|급여/g, "임금"], [/계약을?\s*끝내|계약을?\s*취소/g, "계약 해지"],
  [/돈을?\s*보냈|송금했|이체했/g, "대금 송금"],
  [/잠수(?:를)?\s*(?:탔|타)|연락이?\s*끊/g, "물건 미배송"],
  [/보내지\s*않|안\s*보내|안\s*보냈/g, "미배송"],
  [/되돌려|돌려받|돌려주/g, "반환"], [/유산/g, "상속재산"],
];
function fragments(text: string) {
  let normalized = text.normalize("NFKC").toLowerCase();
  for (const [pattern, replacement] of synonyms)
    normalized = normalized.replace(pattern, replacement);
  const words = normalized.match(/[가-힣a-z0-9]+/g) ?? [];
  const grams = new Set<string>();
  for (const word of words) {
    for (const length of [2, 3])
      for (let at = 0; at + length <= word.length; at++)
        grams.add(word.slice(at, at + length));
  }
  return grams;
}

export function closest<T extends { title: string; summary: string }>(
  description: string, candidates: readonly T[],
): T | undefined {
  const query = fragments(description);
  const docs = candidates.map(item => ({
    item, title: fragments(item.title), body: fragments(item.title + " " + item.summary),
  }));
  const counts = new Map<string, number>();
  for (const doc of docs) for (const gram of doc.body)
    counts.set(gram, (counts.get(gram) ?? 0) + 1);
  let best: T | undefined;
  let bestScore = 0;
  for (const doc of docs) {
    let score = 0;
    let distinctive = 0;
    for (const gram of query) {
      if (!doc.body.has(gram)) continue;
      const frequency = counts.get(gram)!;
      if (frequency <= Math.ceil(docs.length / 2)) distinctive++;
      const weight = Math.log(1 + docs.length / frequency);
      score += weight * (gram.length === 3 ? 1.5 : 1) * (doc.title.has(gram) ? 2 : 1);
    }
    score /= Math.sqrt(Math.max(1, doc.body.size));
    if (distinctive >= 2 && score > bestScore) {
      bestScore = score;
      best = doc.item;
    }
  }
  return best;
}
