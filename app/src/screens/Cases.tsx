import React, { useState } from "react";
import { Text, View, Pressable, Alert, Linking } from "react-native";
import { router, useLocalSearchParams } from "expo-router";
import {
  Screen,
  Heading,
  Button,
  Card,
  Empty,
  Check,
  Field,
  s,
  C,
} from "../components/ui";
import { useApp } from "../state/AppProvider";
import { CaseRecord, todoLabels, validDate } from "../domain/model";
import { CaseCard } from "./Home";
import { isOfficialSource } from "../services/consultation";
export function Cases() {
  const { data } = useApp(),
    [filter, setFilter] = useState("전체");
  const list = data.cases.filter(
    (c) => filter === "전체" || c.status === filter,
  );
  return (
    <Screen>
      <Heading title="내 사건" sub="작은 기록부터 차근차근 관리해요." />
      <View style={[s.row, { marginBottom: 22 }]}>
        {["전체", "진행 중", "완료"].map((t) => (
          <Pressable
            key={t}
            onPress={() => setFilter(t)}
            style={[s.tab, filter === t && s.tabSelected]}
          >
            <Text
              style={{ fontSize: 13, color: filter === t ? "white" : C.muted }}
            >
              {t}{" "}
              {data.cases.filter((c) => t === "전체" || c.status === t).length}
            </Text>
          </Pressable>
        ))}
      </View>
      {list.length ? (
        list.map((c) => <CaseCard key={c.id} item={c} />)
      ) : (
        <Empty
          text={
            filter === "전체"
              ? "아직 저장한 사건이 없어요"
              : `${filter} 사건이 없어요`
          }
        />
      )}
      <View style={{ height: 24 }} />
      <Button
        label="새 상담 시작하기"
        onPress={() => router.push("/categories")}
      />
    </Screen>
  );
}
export function CaseDetail() {
  const { id } = useLocalSearchParams<{ id: string }>(),
    { data, update } = useApp(),
    [tab, setTab] = useState("개요"),
    [editing, setEditing] = useState(false);
  const c = data.cases.find((x) => x.id === id);
  function change(patch: Partial<CaseRecord>, label: string) {
    const at = new Date().toISOString();
    update((d) => ({
      ...d,
      cases: d.cases.map((x) =>
        x.id === id
          ? {
              ...x,
              ...patch,
              updatedAt: at,
              history: [...x.history, { at, label }],
            }
          : x,
      ),
    }));
  }
  if (editing) return <EditCase onDone={() => setEditing(false)} />;
  if (!c)
    return (
      <Screen>
        <Empty
          text="사건을 찾을 수 없어요"
          sub="삭제된 사건이거나 유효하지 않은 주소입니다."
        />
        <Button
          label="내 사건으로"
          onPress={() => router.replace("/(tabs)/cases")}
        />
      </Screen>
    );
  return (
    <Screen
      footer={
        <Button
          label="이어서 상담하기"
          onPress={() => {
            update((d) => ({ ...d, draft: { ...c, caseId: c.id } }));
            router.push("/situation");
          }}
        />
      }
    >
      <Heading
        title={c.title}
        kicker={`${c.category} · ${c.status}`}
        sub={`발생일 ${c.date}`}
      />
      <View style={s.row}>
        <Pressable onPress={() => setEditing(true)}>
          <Text style={s.link}>사건 수정</Text>
        </Pressable>
        <Pressable
          onPress={() =>
            Alert.alert(
              "사건을 삭제할까요?",
              "저장한 내용과 할 일을 삭제합니다. 되돌릴 수 없습니다.",
              [
                { text: "취소", style: "cancel" },
                {
                  text: "삭제",
                  style: "destructive",
                  onPress: () => {
                    update((d) => ({
                      ...d,
                      cases: d.cases.filter((x) => x.id !== id),
                      draft:
                        d.draft.caseId === id
                          ? { ...d.draft, caseId: undefined }
                          : d.draft,
                    }));
                    router.replace("/(tabs)/cases");
                  },
                },
              ],
            )
          }
        >
          <Text style={[s.link, { color: C.danger }]}>삭제</Text>
        </Pressable>
      </View>
      <View style={[s.row, { marginVertical: 16 }]}>
        {["개요", "증거", "기록"].map((t) => (
          <Pressable
            key={t}
            onPress={() => setTab(t)}
            style={[s.tab, tab === t && s.tabSelected]}
          >
            <Text style={{ color: tab === t ? "white" : C.muted }}>{t}</Text>
          </Pressable>
        ))}
      </View>
      {tab === "개요" ? (
        <>
          <Card>
            <Text style={s.h2}>상황 정리</Text>
            <Text selectable style={s.body}>
              {c.description || "상황 정리를 저장하지 않았습니다."}
            </Text>
            {c.amount ? (
              <Text style={s.small}>
                관련 금액 {Number(c.amount).toLocaleString()}원
              </Text>
            ) : null}
            <Text style={s.h2}>저장한 상담 결과</Text>
            <Text style={s.body}>
              {c.result?.summary || "저장한 결과가 없습니다."}
            </Text>
            {c.result?.precedents.map((p) => (
              <View key={p.id}>
                <Text style={s.body}>
                  {p.title} · {p.caseNumber}
                </Text>
                <Text style={s.small}>{p.summary}</Text>
                <Button
                  secondary
                  label="원문 보기"
                  onPress={() => {
                    if (isOfficialSource(p.sourceUrl))
                      void Linking.openURL(p.sourceUrl).catch(() =>
                        Alert.alert("열기 실패"),
                      );
                  }}
                />
              </View>
            ))}
            <Text style={s.h2}>메모</Text>
            <Text style={s.body}>{c.memo || "메모가 없습니다."}</Text>
          </Card>
          <Card>
            <Text style={s.h2}>진행 상태</Text>
            <View style={s.row}>
              {(["진행 중", "완료"] as const).map((status) => (
                <Pressable
                  key={status}
                  onPress={() => {
                    if (c.status !== status)
                      change({ status }, `상태 변경: ${status}`);
                  }}
                  style={[s.tab, c.status === status && s.tabSelected]}
                >
                  <Text
                    style={{ color: c.status === status ? "white" : C.green }}
                  >
                    {status}
                  </Text>
                </Pressable>
              ))}
            </View>
            <Text style={s.small}>
              {c.deadline
                ? `확인할 기한: ${c.deadline}`
                : "설정된 기한이 없습니다."}{" "}
              · 실제 알림 발송 없음
            </Text>
          </Card>
          <Card>
            <Text style={s.h2}>
              해야 할 일 {c.checks.filter(Boolean).length}/3
            </Text>
            {todoLabels.map((t, i) => (
              <Check
                key={t}
                label={t}
                value={c.checks[i]}
                onChange={() =>
                  change(
                    { checks: c.checks.map((v, j) => (i === j ? !v : v)) },
                    `${c.checks[i] ? "할 일 취소" : "할 일 완료"}: ${t}`,
                  )
                }
              />
            ))}
          </Card>
        </>
      ) : tab === "증거" ? (
        <Card>
          <Text style={s.h2}>첨부자료 목록</Text>
          <Text style={s.small}>원본 파일은 저장하지 않습니다.</Text>
          {c.evidence.length ? (
            c.evidence.map((f) => (
              <Text key={f.id} style={s.body}>
                {f.name}
                {"\n"}
                <Text style={s.small}>{Math.ceil(f.size / 1024)}KB</Text>
              </Text>
            ))
          ) : (
            <Text style={s.body}>첨부한 자료가 없습니다.</Text>
          )}
        </Card>
      ) : (
        <Card>
          <Text style={s.h2}>사건 타임라인</Text>
          <View style={s.timeline}>
            {[...c.history].reverse().map((h, i) => (
              <View key={`${h.at}-${i}`}>
                <Text style={s.body}>{h.label}</Text>
                <Text style={s.small}>
                  {new Date(h.at).toLocaleString("ko-KR")}
                </Text>
              </View>
            ))}
          </View>
        </Card>
      )}
    </Screen>
  );
}
function EditCase({ onDone }: { onDone: () => void }) {
  const { id } = useLocalSearchParams<{ id: string }>(),
    { data, update } = useApp(),
    c = data.cases.find((x) => x.id === id),
    [title, setTitle] = useState(c?.title || ""),
    [memo, setMemo] = useState(c?.memo || ""),
    [deadline, setDeadline] = useState(c?.deadline || ""),
    [error, setError] = useState("");
  if (!c)
    return (
      <Screen>
        <Empty text="사건을 찾을 수 없어요" />
      </Screen>
    );
  return (
    <Screen
      footer={
        <Button
          label="변경 내용 저장"
          onPress={() => {
            if (!title.trim()) {
              setError("제목을 입력해 주세요.");
              return;
            }
            if (deadline && !validDate(deadline)) {
              setError("기한을 실제 날짜로 입력해 주세요.");
              return;
            }
            const at = new Date().toISOString();
            update((d) => ({
              ...d,
              cases: d.cases.map((x) =>
                x.id === id
                  ? {
                      ...x,
                      title: title.trim(),
                      memo,
                      deadline,
                      updatedAt: at,
                      history: [...x.history, { at, label: "사건 정보 수정" }],
                    }
                  : x,
              ),
            }));
            onDone();
          }}
        />
      }
    >
      <Heading title="사건 수정" />
      <Button label="수정 취소" secondary onPress={onDone} />
      <Field
        label="사건 제목"
        value={title}
        onChangeText={setTitle}
        maxLength={80}
      />
      <Field
        label="확인할 기한 (선택)"
        value={deadline}
        onChangeText={setDeadline}
        placeholder="YYYY-MM-DD"
        maxLength={10}
      />
      <Field
        label="메모"
        value={memo}
        onChangeText={setMemo}
        multiline
        maxLength={1000}
      />
      {error ? <Text style={s.error}>{error}</Text> : null}
    </Screen>
  );
}
