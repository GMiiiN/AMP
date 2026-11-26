import React, { useState } from "react";
import { Linking } from "react-native";
import { WebView } from "react-native-webview";
import { suggestionNavigation } from "../services/officialSource";
import { suggestionDocument } from "./suggestionDocument";

// 그린 뒤 실제 높이를 알려 주어 WebView 높이를 내용에 맞춘다.
const REPORT_HEIGHT = "window.ReactNativeWebView.postMessage(String(document.body.scrollHeight)); true;";

function handle(url: string) {
  const action = suggestionNavigation(url);
  if (action === "external") void Linking.openURL(url).catch(() => undefined);
  return action === "load";
}

/** 웹 검색 답변과 함께 보여 줘야 하는 Google Search Suggestions. 링크는 외부 브라우저로 열고 그 밖의 탐색은 막는다. */
export function SearchSuggestions({ html }: { html?: string | null }) {
  const [height, setHeight] = useState(64);
  if (!html) return null;
  return <WebView
    originWhitelist={["*"]}
    source={{ html: suggestionDocument(html) }}
    style={{ height, backgroundColor: "transparent" }}
    scrollEnabled={false}
    injectedJavaScript={REPORT_HEIGHT}
    onMessage={(e) => { const h = Number(e.nativeEvent.data); if (h > 0) setHeight(Math.ceil(h)); }}
    onShouldStartLoadWithRequest={(request) => handle(request.url)}
    onOpenWindow={(e) => { handle(e.nativeEvent.targetUrl); }}
  />;
}
