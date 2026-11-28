import React from "react";
import { Alert, Linking, Text, View } from "react-native";
import { Button, s } from "./ui";
import type { WebSource } from "../domain/model";
import { openWebSource, webSourceHostNote, webUrlHost } from "../services/officialSource";

/** 기타 분야 답변이 참고한 Google 검색 출처. 누르면 확인 창 없이 외부 브라우저로 연다. 없으면 아무것도 그리지 않는다. */
export function WebSources({ items }: { items?: WebSource[] }) {
  if (!items?.length) return null;
  return <View style={{ gap: 8 }}>
    <Text style={s.badge}>참고한 웹 검색 출처</Text>
    {items.map(item => {
      const host = webUrlHost(item.url);
      return <View key={item.url} style={{ gap: 4 }}>
        <Button secondary label={item.title} onPress={() => openWebSource(item.url, Alert.alert, Linking.openURL)} />
        {host ? <Text style={s.small}>{webSourceHostNote(host)}</Text> : null}
      </View>;
    })}
    <Text style={s.small}>Google 검색으로 찾은 자료입니다. 내 상황과 다를 수 있으니 내용을 직접 확인해 주세요.</Text>
  </View>;
}
