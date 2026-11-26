/**
 * Search Suggestions HTML 을 그대로(수정 없이) 감싸 모바일 화면 폭에 맞춘 문서로 만든다.
 * 약관이 Search Suggestions 수정을 금지하므로 링크 주소나 target 은 바꾸지 않고,
 * 네이티브는 WebView 탐색 규칙, 웹은 iframe sandbox 로 탐색을 제한한다.
 */
export function suggestionDocument(html: string, linkTarget?: "_blank") {
  const base = linkTarget ? `<base target="${linkTarget}">` : "";
  return `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">${base}</head><body style="margin:0">${html}</body></html>`;
}
/** Search Suggestions 가 그려진 뒤 알려 준 높이. 숫자가 아니거나 0 이하면 무시하고, 너무 크면 상한으로 자른다. */
export const SUGGESTION_MAX_HEIGHT = 400;
export function suggestionHeight(value: unknown): number | null {
  const height = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(height) || height <= 0) return null;
  return Math.min(Math.ceil(height), SUGGESTION_MAX_HEIGHT);
}
