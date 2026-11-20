import React, { useState } from "react";
import { Alert, Linking, Text, View, Modal, FlatList } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Button, s, C } from "./ui";
import type { Precedent } from "../domain/model";
import details from "../domain/judgmentDetails.json";
import { isOfficialSource } from "../services/consultation";

export function SimilarPrecedent({ item }: { item?: Precedent }) {
  const [openedId, setOpenedId] = useState<string | null>(null);
  const candidate = item ? details[item.id as keyof typeof details] : undefined;
  const detail = candidate?.number === item?.caseNumber ? candidate : undefined;
  const openSource = () => {
    if (item && isOfficialSource(item.sourceUrl))
      void Linking.openURL(item.sourceUrl).catch(() => Alert.alert("원문을 열 수 없어요", "인터넷 연결을 확인해 주세요."));
  };
  return <View style={{ gap: 12 }}>
    <Text style={s.badge}>내 상황과 유사한 판례 · 최대 1건</Text>
    {item ? <>
      <Text style={s.h2}>{item.title}</Text>
      <Text selectable style={s.small}>{item.court} · {item.judgmentDate} · {item.caseNumber}</Text>
      <Text style={s.body}>{item.summary}</Text>
      <Text style={s.small}>출처: 국가법령정보센터 · 표현이나 내용이 유사한 참고 판례입니다. 사실관계와 법적 쟁점은 다를 수 있습니다.</Text>
      {detail && <Button label="판결 내용 자세히 보기" secondary onPress={() => setOpenedId(item.id)} />}
      <Button secondary label="국가법령정보센터 원문 보기" onPress={openSource} />
      {detail && <Modal visible={openedId === item.id} animationType="slide" onRequestClose={() => setOpenedId(null)}>
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
