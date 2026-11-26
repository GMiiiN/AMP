import React, { useRef, useState } from "react";
import { Linking } from "react-native";
import { WebView } from "react-native-webview";
import { suggestionNavigation, type SuggestionRequest } from "../services/officialSource";
import { suggestionDocument, suggestionHeight } from "./suggestionDocument";

// 그린 뒤 실제 높이를 알려 주어 WebView 높이를 내용에 맞춘다.
const REPORT_HEIGHT = "window.ReactNativeWebView.postMessage(String(document.body.scrollHeight)); true;";

/** 웹 검색 답변과 함께 보여 줘야 하는 Google Search Suggestions. 링크는 외부 브라우저로 열고 그 밖의 탐색은 막는다. */
export function SearchSuggestions({ html }: { html?: string | null }) {
  const [height, setHeight] = useState(64);
  // 처음 문서를 그린 뒤에는 about:blank·data: 탐색을 막기 위한 표시. Android 는 첫 로드에 탐색 요청을 보내지 않을 수 있어 onLoad 에서도 세운다.
  const loaded = useRef(false);
  if (!html) return null;
  const handle = (request: SuggestionRequest) => {
    const action = suggestionNavigation(request, loaded.current);
    if (action === "load") loaded.current = true;
    if (action === "external") void Linking.openURL(request.url).catch(() => undefined);
    return action === "load";
  };
  return <WebView
    originWhitelist={["*"]}
    source={{ html: suggestionDocument(html) }}
    style={{ height, backgroundColor: "transparent" }}
    scrollEnabled={false}
    setSupportMultipleWindows={false}
    injectedJavaScript={REPORT_HEIGHT}
    onLoad={() => { loaded.current = true; }}
    onMessage={(e) => { const h = suggestionHeight(e.nativeEvent.data); if (h !== null) setHeight(h); }}
    onShouldStartLoadWithRequest={handle}
  />;
}
