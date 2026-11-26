import React, { useState } from "react";
import { Alert, Linking, Text, View, Modal, FlatList, ScrollView } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Button, s, C } from "./ui";
import type { Precedent } from "../domain/model";
import details from "../domain/judgmentDetails.json";
import { isOfficialSource } from "../services/consultation";

function SimilarPrecedent({ item, compact = false }: { item?: Precedent; compact?: boolean }) {
  const [openedId, setOpenedId] = useState<string | null>(null);
  const candidate = item ? details[item.id as keyof typeof details] : undefined;
  const detail = candidate?.number === item?.caseNumber ? candidate : undefined;
  const openSource = () => {
    if (item && isOfficialSource(item.sourceUrl))
      void Linking.openURL(item.sourceUrl).catch(() => Alert.alert("원문을 열 수 없어요", "인터넷 연결을 확인해 주세요."));
  };
  return <View style={{ gap: 12 }}>
    <Text style={s.badge}>{compact ? "함께 참고할 유사 판례" : "내 상황과 가장 유사한 판례"}</Text>
    {item ? <>
      <Text style={s.h2}>{item.title}</Text>
      <Text selectable style={s.small}>{item.court} · {item.judgmentDate} · {item.caseNumber}</Text>
      <Text style={s.body}>{item.summary}</Text>
      <Text style={s.small}>출처: 국가법령정보센터 · 표현이나 내용이 유사한 참고 판례입니다. 사실관계와 법적 쟁점은 다를 수 있습니다.</Text>
      {detail && !compact && <View style={{ gap: 8 }}>
        <Text style={s.h2}>판결 상세 내용</Text>
        <Text style={s.small}>공식 원문의 주문·판결 이유입니다. 아래 영역을 스크롤해서 읽을 수 있어요.</Text>
        <ScrollView nestedScrollEnabled style={{ height: 320 }} contentContainerStyle={{ gap: 12, padding: 12 }}>
          {["주문", ...detail.order, "판결 이유", ...detail.reasons].map((text, index) =>
            <Text key={index} selectable style={[s.body, { lineHeight: 26 }]}>{text}</Text>)}
        </ScrollView>
      </View>}
      {!detail && !compact && <Text style={s.small}>이 판례의 상세본문은 아래 공식 원문에서 확인해 주세요.</Text>}
      {detail && !compact && <Button label="판결 내용 자세히 보기" secondary onPress={() => setOpenedId(item.id)} />}
      <Button secondary label="국가법령정보센터 원문 보기" onPress={openSource} />
      {detail && !compact && <Modal visible={openedId === item.id} animationType="slide" onRequestClose={() => setOpenedId(null)}>
        <SafeAreaView style={{ flex: 1, backgroundColor: C.bg }}>
          <View style={{ padding: 20, gap: 10 }}>
            <Text style={s.h2}>판결 내용</Text>
            <Text selectable style={s.small}>{item.court} · {item.caseNumber}</Text>
            <Button secondary label="닫기" onPress={() => setOpenedId(null)} />
          </View>
          <FlatList
            data={["주문", ...detail.order, "판결 이유", ...detail.reasons]}
            keyExtractor={(_, index) => String(index)}
            contentContainerStyle={{ padding: 20, gap: 14 }}
            renderItem={({ item: paragraph }) => <Text selectable style={[s.body, { lineHeight: 26 }]}>{paragraph}</Text>}
            ListHeaderComponent={<Text style={[s.small, { marginBottom: 16 }]}>국가법령정보센터 공개 원문의 주문과 판결 이유입니다. 당사자 표기·참조조문·별지 등 전체 구성은 원문에서 확인해 주세요.</Text>}
            ListFooterComponent={<Button secondary label="공식 원문에서 전체 보기" onPress={openSource} />}
          />
        </SafeAreaView>
      </Modal>}
    </> : <Text style={s.body}>입력한 상황과 연결할 판례를 찾지 못했어요. 어떤 일이 있었는지 구체적으로 적어 주세요.</Text>}
  </View>;
}

export function SimilarPrecedents({ items }: { items: Precedent[] }) {
  const unique = items.filter((item, index) => items.findIndex(other => other.id === item.id) === index).slice(0, 3);
  return <View style={{ gap: 24 }}>
    <SimilarPrecedent key={unique[0]?.id ?? "empty"} item={unique[0]} />
    {unique.length > 1 && <View style={{ gap: 16 }}>
      <Text style={s.h2}>추가로 참고할 유사 판례</Text>
      {unique.slice(1).map(item => <View key={item.id} style={{ borderTopWidth: 1, borderColor: C.line, paddingTop: 16 }}>
        <SimilarPrecedent item={item} compact />
      </View>)}
    </View>}
    {unique.length > 0 && unique.length < 3 && <Text style={s.small}>유사도 기준을 충족한 판례 {unique.length}건을 표시합니다.</Text>}
  </View>;
}
