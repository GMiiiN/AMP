/** Search Suggestions HTML 을 그대로(수정 없이) 감싸 모바일 화면 폭에 맞춘 문서로 만든다. */
export function suggestionDocument(html: string, linkTarget?: "_blank") {
  const base = linkTarget ? `<base target="${linkTarget}">` : "";
  return `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">${base}</head><body style="margin:0">${html}</body></html>`;
}
