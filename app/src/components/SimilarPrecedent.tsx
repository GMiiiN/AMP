import React from "react";
import { Alert, Linking, Text, View } from "react-native";
import { Button, s } from "./ui";
import { formatJudgmentDate, type Precedent } from "../domain/model";
import { confirmOpenSource } from "../services/officialSource";

function PrecedentItem({ item }: { item: Precedent }) {
  return <View style={{ gap: 8 }}>
    {item.cited ? <Text style={s.badge}>답변에서 인용</Text> : null}
    <Text style={s.h2}>{item.title}</Text>
    <Text selectable style={s.small}>{item.court} · {formatJudgmentDate(item.judgmentDate)} · {item.caseNumber}</Text>
    <Text style={s.body}>{item.summary}</Text>
    <Button secondary label="국가법령정보센터 원문 보기" onPress={() => confirmOpenSource(item.sourceUrl, Alert.alert, Linking.openURL)} />
  </View>;
}

/** 서버가 유사도 순으로 보낸 판례 중 첫 건을 "가장 유사한 판례", 나머지를 "비슷한 판례"로 보여 준다. */
export function SimilarPrecedent({ items }: { items: Precedent[] }) {
  const [best, ...others] = items;
  if (!best) return <Text style={s.body}>표시할 판례가 없어요.</Text>;
  return <View style={{ gap: 12 }}>
    <Text style={s.badge}>가장 유사한 판례</Text>
    <PrecedentItem item={best} />
    {others.length ? <Text style={s.badge}>비슷한 판례</Text> : null}
    {others.map(item => <PrecedentItem key={item.id} item={item} />)}
    <Text style={s.small}>출처: 국가법령정보센터 · 판례 제목과 설명은 앱에서 정리한 문장입니다. 사실관계와 법적 쟁점은 다를 수 있으니 원문을 확인해 주세요.</Text>
  </View>;
}
