import React from "react";
import { suggestionDocument } from "./suggestionDocument";

/** 웹 빌드용: react-native-webview 가 없으므로 sandbox iframe 으로 그린다. 링크는 새 탭으로 열리고 iframe 안 탐색은 막힌다. */
export function SearchSuggestions({ html }: { html?: string | null }) {
  if (!html) return null;
  return React.createElement("iframe", {
    title: "Google 검색 제안",
    srcDoc: suggestionDocument(html, "_blank"),
    sandbox: "allow-popups allow-popups-to-escape-sandbox",
    style: { border: 0, width: "100%", height: 72 },
  });
}
