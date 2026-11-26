import React from "react";
import { Alert, Linking, Text, View } from "react-native";
import { Button, s } from "./ui";
import type { WebSource } from "../domain/model";
import { confirmOpenWebSource } from "../services/officialSource";

/** 기타 분야 답변이 참고한 Google 검색 출처. 없으면 아무것도 그리지 않는다. */
export function WebSources({ items }: { items?: WebSource[] }) {
  if (!items?.length) return null;
  return <View style={{ gap: 8 }}>
    <Text style={s.badge}>참고한 웹 검색 출처</Text>
    {items.map(item => <Button key={item.url} secondary label={item.title} onPress={() => confirmOpenWebSource(item.url, Alert.alert, Linking.openURL)} />)}
    <Text style={s.small}>Google 검색으로 찾은 자료입니다. 내 상황과 다를 수 있으니 내용을 직접 확인해 주세요.</Text>
  </View>;
}
