import React, { useState } from "react";
import { Text, View, Pressable } from "react-native";
import { router } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import {
  Screen,
  Heading,
  Button,
  Notice,
  Section,
  Field,
  Empty,
  s,
  C,
} from "../components/ui";
import { categories, Category, CaseRecord } from "../domain/model";
import { usesApi } from "../services/consultation";
import { useApp } from "../state/AppProvider";
export function CaseCard({ item }: { item: CaseRecord }) {
  return (
    <Pressable
      accessibilityRole="button"
      onPress={() =>
        router.push({ pathname: "/case-detail", params: { id: item.id } })
      }
      style={s.card}
    >
      <View style={s.row}>
        <Text style={s.badge}>{item.category}</Text>
        <Text style={s.small}>{item.status}</Text>
      </View>
      <Text style={s.h2}>{item.title}</Text>
      <Text style={s.body} numberOfLines={2}>
        {item.description || "저장한 사건 정보를 확인하세요."}
      </Text>
      <View style={s.bar}>
        <View
          style={{
            width: `${(item.checks.filter(Boolean).length / 3) * 100}%`,
            height: 5,
            backgroundColor: "#809F60",
          }}
        />
      </View>
      <Text style={s.small}>
        할 일 {item.checks.filter(Boolean).length}/3 ·{" "}
        {item.deadline ? `기한 ${item.deadline}` : item.date}
      </Text>
    </Pressable>
  );
}
export function CategoryGrid({ compact = false }: { compact?: boolean }) {
  const { update } = useApp();
  function select(name: Category) {
    update((d) => ({ ...d, draft: { ...d.draft, category: name } }));
    router.push("/situation");
  }
  return (
    <View style={s.grid}>
      {(compact ? categories.slice(0, 4) : categories).map((c, i) => (
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={`${c.name} 상담 시작`}
          key={c.name}
          onPress={() => select(c.name)}
          style={s.category}
        >
          <View
            style={[s.iconbox, i % 3 === 1 && { backgroundColor: "#EDF2F3" }]}
          >
            <Ionicons name={c.icon} size={23} color={C.green} />
          </View>
          <Text style={[s.h2, { fontSize: 15 }]}>{c.name}</Text>
          <Text style={s.small}>{c.description}</Text>
        </Pressable>
      ))}
    </View>
  );
}
export default function Home() {
  const { data, update } = useApp(),
    [search, setSearch] = useState("");
  return (
    <Screen>
      <Heading
        kicker="나의 일상에, 법률 길잡이"
        title={`${data.profile?.name || "방문자"}님,\n어떤 고민이 있으신가요?`}
        sub="막막한 상황을 하나씩 정리해 보세요."
      />
      <View style={s.hero}>
        <View style={s.row}>
          <Text style={{ color: C.lime, fontSize: 11, letterSpacing: 1 }}>
            EVERYDAY LEGAL GUIDE
          </Text>
          <Ionicons name="scale-outline" size={38} color={C.lime} />
        </View>
        <Text
          style={{
            color: "white",
            fontSize: 25,
            fontWeight: "700",
            lineHeight: 36,
          }}
        >
          어려운 법률 용어 대신,{"\n"}내 이야기부터.
        </Text>
        <Text style={{ color: "#CAD8C9", lineHeight: 22, fontSize: 13 }}>
          상황을 정리하고 다음 상담에{"\n"}필요한 정보를 차근차근 준비해요.
        </Text>
        <Button
          label="법률 상담 시작하기"
          icon="arrow-forward"
          secondary
          onPress={() => router.push("/categories")}
        />
      </View>
      <Field
        label="어떤 일이 있었나요?"
        value={search}
        onChangeText={setSearch}
        placeholder="간단히 적고 상담을 시작해 보세요"
        maxLength={1000}
        returnKeyType="go"
        onSubmitEditing={() => {
          if (search.trim()) {
            update((d) => ({
              ...d,
              draft: { ...d.draft, description: search },
            }));
            router.push("/categories");
          }
        }}
      />
      {search.trim() ? (
        <Button
          secondary
          label="이 내용으로 상담 시작"
          onPress={() => {
            update((d) => ({
              ...d,
              draft: { ...d.draft, description: search },
            }));
            router.push("/categories");
          }}
        />
      ) : null}
      <Section title="자주 찾는 분야">
        <Pressable onPress={() => router.push("/categories")}>
          <Text style={s.link}>전체 보기 →</Text>
        </Pressable>
      </Section>
      <CategoryGrid compact />
      <Section title="진행 중인 내 사건">
        <Pressable onPress={() => router.push("/(tabs)/cases")}>
          <Text style={s.link}>모두 보기</Text>
        </Pressable>
      </Section>
      {data.cases
        .filter((c) => c.status === "진행 중")
        .slice(0, 2)
        .map((item) => (
          <CaseCard key={item.id} item={item} />
        ))}
      {!data.cases.some((c) => c.status === "진행 중") ? <Empty /> : null}
      <View style={{ height: 24 }} />
      <Notice>
        {usesApi
          ? "개발용 API 연결 모드입니다. 서버 설정에 따라 데모·검색·AI 요약이 제공됩니다."
          : "프론트엔드 체험판 · AI와 판례 API 연결 전입니다."}{" "}
        실제 개인정보 대신 예시 내용으로 사용해 주세요.
      </Notice>
    </Screen>
  );
}
export function Categories() {
  return (
    <Screen>
      <Heading
        title="어떤 문제인가요?"
        sub="가장 가까운 분야를 선택해 주세요."
      />
      <CategoryGrid />
      <View style={{ height: 22 }} />
      <Notice>
        어떤 분야인지 모르겠다면 기타를 선택하세요. 기타 분야는 판례 검색
        대상에서 제외됩니다.
      </Notice>
    </Screen>
  );
}
