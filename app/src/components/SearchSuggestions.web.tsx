import React, { useState } from "react";
import { suggestionDocument, suggestionHeight } from "./suggestionDocument";

/**
 * 웹 빌드용: react-native-webview 가 없으므로 sandbox iframe 으로 그린다.
 * sandbox 에 allow-scripts·allow-top-navigation 이 없어 문서 안 스크립트와 상위 창 이동은 막히고,
 * 링크는 <base target="_blank"> 로 새 탭에서 열린다. allow-same-origin 은 스크립트 없이 높이만 읽기 위해 둔다.
 */
export function SearchSuggestions({ html }: { html?: string | null }) {
  const [height, setHeight] = useState(96);
  if (!html) return null;
  return React.createElement("iframe", {
    title: "Google 검색 제안",
    srcDoc: suggestionDocument(html, "_blank"),
    sandbox: "allow-popups allow-popups-to-escape-sandbox allow-same-origin",
    style: { border: 0, width: "100%", height },
    onLoad: (e: { currentTarget: HTMLIFrameElement }) => {
      const h = suggestionHeight(e.currentTarget.contentDocument?.body?.scrollHeight);
      if (h !== null) setHeight(h);
    },
  });
}
