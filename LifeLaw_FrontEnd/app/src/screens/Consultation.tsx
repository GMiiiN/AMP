import React, { useState, useEffect } from "react";
import {
  Text,
  View,
  Pressable,
  Alert,
  ActivityIndicator,
  Linking,
} from "react-native";
import { router } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import * as DocumentPicker from "expo-document-picker";
import {
  Screen,
  Heading,
  Button,
  Notice,
  Field,
  Card,
  Check,
  Step,
  s,
  C,
} from "../components/ui";
import { useApp } from "../state/AppProvider";
import {
  categories,
  validateDraft,
  questions,
  todoLabels,
  makeCase,
  emptyDraft,
  validDate,
} from "../domain/model";
import {
  consultationService,
  usesApi,
  ConsultationResult,
} from "../services/consultation";
export function Situation() {
  const { data, update } = useApp(),
    d = data.draft,
    [error, setError] = useState(""),
    [picking, setPicking] = useState(false);
  function patch(change: Partial<typeof d>) {
    update((a) => ({
      ...a,
      draft: { ...a.draft, result: undefined, ...change },
    }));
  }
  async function pick() {
    setPicking(true);
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: ["image/*", "audio/*", "application/pdf", "text/plain"],
        multiple: true,
        copyToCacheDirectory: false,
      });
      if (result.canceled) return;
      const accepted = result.assets.filter(
        (a) => a.size !== undefined && a.size <= 10 * 1024 * 1024,
      );
      if (accepted.length !== result.assets.length)
        Alert.alert(
          "첨부 제한",
          "크기를 확인할 수 없거나 10MB를 넘는 파일은 제외했습니다.",
        );
      const room = Math.max(0, 5 - d.evidence.length);
      if (accepted.length > room)
        Alert.alert("첨부 제한", "최대 5개까지만 첨부할 수 있습니다.");
      patch({
        evidence: [
          ...d.evidence,
          ...accepted
            .slice(0, room)
            .map((a, i) => ({
              id: `${Date.now()}-${i}`,
              name: a.name,
              size: a.size || 0,
              mimeType: a.mimeType || "application/octet-stream",
            })),
        ],
      });
    } catch {
      Alert.alert(
        "선택 실패",
        "파일을 선택하지 못했습니다. 다시 시도해 주세요.",
      );
    } finally {
      setPicking(false);
    }
  }
  return (
    <Screen
      footer={
        <Button
          label="추가 질문으로"
          icon="arrow-forward"
          onPress={() => {
            const msg = validateDraft(d);
            setError(msg);
            if (!msg) router.push("/questions");
          }}
        />
      }
    >
      <Heading
        title="어떤 일이 있었나요?"
        sub="기억나는 사실부터 편하게 적어 주세요."
      />
      <Step current={0} />
      <Text style={s.label}>상담 분야</Text>
      <View style={[s.grid, { marginTop: 12, marginBottom: 22 }]}>
        {categories.map((c) => (
          <Pressable
            key={c.name}
            onPress={() => patch({ category: c.name })}
            style={[
              s.chip,
              d.category === c.name && { backgroundColor: C.green },
            ]}
          >
            <Text
              style={{
                color: d.category === c.name ? "white" : C.green,
                fontSize: 13,
              }}
            >
              {c.name}
            </Text>
          </Pressable>
        ))}
      </View>
      <Field
        label="발생일"
        placeholder="YYYY-MM-DD · 예: 2026-10-01"
        value={d.date}
        onChangeText={(date) => patch({ date })}
        maxLength={10}
        keyboardType="numbers-and-punctuation"
      />
      <Field
        label="관련 금액 (선택 · 원)"
        placeholder="숫자만 입력해 주세요"
        value={d.amount}
        onChangeText={(amount) => patch({ amount })}
        keyboardType="number-pad"
        maxLength={12}
      />
      <Field
        label="어떤 일이 있었나요?"
        placeholder="누가, 언제, 어디서, 어떤 일이 있었나요?"
        value={d.description}
        onChangeText={(description) => patch({ description })}
        multiline
        maxLength={1000}
      />
      <Text
        style={[
          s.small,
          { textAlign: "right", marginTop: -10, marginBottom: 20 },
        ]}
      >
        {d.description.length} / 1000자
      </Text>
      <Card>
        <Text style={s.h2}>
          증거 첨부 <Text style={s.small}>(선택)</Text>
        </Text>
        <Button
          secondary
          label={picking ? "파일 선택 중…" : "사진 · 문서 · 녹음 파일 선택"}
          onPress={() => void pick()}
          disabled={picking || d.evidence.length >= 5}
          icon="attach-outline"
        />
        {d.evidence.map((f) => (
          <View key={f.id} style={s.row}>
            <Text style={[s.small, { flex: 1 }]}>
              {f.name} · {Math.ceil(f.size / 1024)}KB
            </Text>
            <Pressable
              accessibilityLabel={`${f.name} 삭제`}
              style={{ padding: 12 }}
              onPress={() =>
                patch({ evidence: d.evidence.filter((x) => x.id !== f.id) })
              }
            >
              <Ionicons name="close-circle-outline" size={22} color={C.muted} />
            </Pressable>
          </View>
        ))}
        <Text style={s.small}>
          5개까지, 파일당 10MB. 현재는 파일명·크기만 저장하며 원본은
          업로드하거나 보관하지 않습니다.
        </Text>
      </Card>
      {error ? (
        <Text accessibilityRole="alert" style={s.error}>
          {error}
        </Text>
      ) : null}
      <Notice>
        입력 내용은 이 기기에 임시 저장됩니다. 실명, 주민등록번호, 계좌번호 등
        민감한 정보는 입력하지 마세요.
      </Notice>
    </Screen>
  );
}
export function Questions() {
  const { data, update } = useApp(),
    [index, setIndex] = useState(0),
    [list, setList] = useState<string[]>([]),
    [error, setError] = useState(""),
    [retry, setRetry] = useState(0);
  const d = data.draft;
  useEffect(() => {
    let active = true;
    consultationService
      .getQuestions(d)
      .then((q) => {
        if (active) setList(q);
      })
      .catch(() => {
        if (active)
          setError(
            "질문을 불러오지 못했어요. 이전 화면에서 다시 시도해 주세요.",
          );
      });
    return () => {
      active = false;
    };
  }, [d.category, retry]);
  function answer(value: string) {
    update((a) => {
      const answers = [...a.draft.answers];
      answers[index] = value;
      return { ...a, draft: { ...a.draft, result: undefined, answers } };
    });
  }
  function next(skip = false) {
    if (skip) answer("건너뜀");
    else if (!d.answers[index]?.trim()) {
      setError("답변을 선택하거나 건너뛰기를 눌러 주세요.");
      return;
    }
    setError("");
    if (index < 2) setIndex(index + 1);
    else router.push("/result");
  }
  const choices =
    index === 2
      ? [
          "상황과 사실관계 정리",
          "준비할 자료 확인",
          "전문 상담 준비",
          "잘 모르겠어요",
        ]
      : ["네", "아니요", "일부만 확인했어요", "잘 모르겠어요"];
  return (
    <Screen
      footer={
        <>
          <Button
            label={index === 2 ? "정리 결과 보기" : "다음 질문"}
            onPress={() => next()}
            disabled={!list.length}
          />
          <View style={s.row}>
            <Pressable
              onPress={() => (index > 0 ? setIndex(index - 1) : router.back())}
            >
              <Text style={s.link}>이전</Text>
            </Pressable>
            <Pressable onPress={() => next(true)} disabled={!list.length}>
              <Text style={s.link}>건너뛰기</Text>
            </Pressable>
          </View>
        </>
      }
    >
      <Heading
        title="조금만 더 알려 주세요"
        sub="답하기 어려운 질문은 건너뛰어도 괜찮아요."
      />
      <Step current={1} />
      <Notice>
        {usesApi
          ? "서버의 분야별 질문으로 사실관계를 확인합니다."
          : "분야별 체험 질문입니다. API 연결 전입니다."}
      </Notice>
      <Text style={s.badge}>
        {d.category} · 질문 {index + 1} / 3
      </Text>
      <View style={[s.bar, { marginVertical: 18 }]}>
        <View
          style={{
            width: `${((index + 1) / 3) * 100}%`,
            height: 5,
            backgroundColor: "#809F60",
          }}
        />
      </View>
      {!list.length ? (
        <ActivityIndicator />
      ) : (
        <Text style={[s.h1, { fontSize: 23, marginBottom: 24 }]}>
          {list[index]}
        </Text>
      )}
      {choices.map((c) => (
        <Pressable
          accessibilityRole="radio"
          accessibilityState={{ checked: d.answers[index] === c }}
          key={c}
          onPress={() => answer(c)}
          style={[s.option, d.answers[index] === c && s.selected]}
        >
          <Ionicons
            name={
              d.answers[index] === c ? "radio-button-on" : "radio-button-off"
            }
            size={22}
            color={C.green}
          />
          <Text style={s.body}>{c}</Text>
        </Pressable>
      ))}
      <Field
        label="직접 설명하기 (선택)"
        value={choices.includes(d.answers[index]) ? "" : d.answers[index] || ""}
        onChangeText={answer}
        placeholder="보기로 답하기 어렵다면 직접 적어 주세요"
        multiline
        maxLength={1000}
      />
      {error ? (
        <>
          <Text style={s.error}>{error}</Text>
          <Button
            secondary
            label="질문 다시 불러오기"
            onPress={() => {
              setError("");
              setRetry((v) => v + 1);
            }}
          />
        </>
      ) : null}
    </Screen>
  );
}
export function Result() {
  const { data, update } = useApp(),
    [result, setResult] = useState<ConsultationResult | null>(null),
    [error, setError] = useState(""),
    [retry, setRetry] = useState(0);
  const d = data.draft;
  useEffect(() => {
    let active = true;
    consultationService
      .getResult(d)
      .then((r) => {
        if (active) {
          setResult(r);
          update((a) => ({ ...a, draft: { ...a.draft, result: r } }));
        }
      })
      .catch(() => {
        if (active)
          setError(
            "결과를 불러오지 못했어요. 서버 연결과 설정을 확인해 주세요.",
          );
      });
    return () => {
      active = false;
    };
  }, [d.category, d.description, retry]);
  return (
    <Screen
      footer={
        <>
          <Button
            label="내 사건으로 저장"
            icon="folder-outline"
            onPress={() => router.push("/save")}
            disabled={!result}
          />
          <Button
            label="내용 수정하기"
            secondary
            onPress={() => router.push("/situation")}
          />
        </>
      }
    >
      <Heading
        title="상황을 정리했어요"
        sub="작성한 내용을 살펴보고 다음 상담을 준비하세요."
      />
      <Step current={2} />
      <Notice>
        법률정보 제공이며 법률 자문이 아닙니다.{" "}
        {result?.mode === "rag"
          ? "AI 요약을 원문과 대조해 주세요."
          : result?.mode === "retrieval"
            ? "판례 검색 결과를 제공합니다. AI 분석은 포함되지 않습니다."
            : "현재는 입력 내용을 정리하는 데모 모드입니다."}
      </Notice>
      {error ? (
        <>
          <Text style={s.error}>{error}</Text>
          <Button
            label="불러오기 재시도"
            onPress={() => {
              setError("");
              setRetry((v) => v + 1);
            }}
          />
        </>
      ) : !result ? (
        <ActivityIndicator />
      ) : (
        <>
          <Card>
            <Text style={s.badge}>
              01 · {result.mode === "demo" ? "내가 입력한 상황" : "상담 정리"}
            </Text>
            <Text selectable style={[s.body, { color: C.text }]}>
              {result.summary}
            </Text>
            <Text style={s.small}>
              {d.category} · {d.date}
              {d.amount ? ` · ${Number(d.amount).toLocaleString()}원` : ""}
            </Text>
            {questions(d.category).map((q, i) => (
              <View key={q}>
                <Text style={s.small}>{q}</Text>
                <Text style={s.body}>{d.answers[i] || "건너뜀"}</Text>
              </View>
            ))}
          </Card>
          <Card>
            <Text style={s.badge}>02 · 관련 법률 · 근거 판례</Text>
            {!result.precedents.length ? (
              <Text style={s.h2}>판례 근거 없음</Text>
            ) : (
              result.precedents.map((p) => (
                <View key={p.id} style={{ gap: 8 }}>
                  <Text style={s.h2}>{p.title}</Text>
                  <Text style={s.small}>
                    {p.caseNumber} · {p.court} · {p.judgmentDate}
                  </Text>
                  <Text style={s.body}>{p.summary}</Text>
                  <Button
                    secondary
                    label="판례 원문 보기"
                    onPress={() =>
                      Alert.alert(
                        "외부 페이지 열기",
                        "국가법령정보센터 원문 페이지로 이동합니다.",
                        [
                          { text: "취소", style: "cancel" },
                          {
                            text: "열기",
                            onPress: () =>
                              void Linking.openURL(p.sourceUrl).catch(() =>
                                Alert.alert(
                                  "열기 실패",
                                  "원문 주소를 확인해 주세요.",
                                ),
                              ),
                          },
                        ],
                      )
                    }
                  />
                </View>
              ))
            )}
            <Text style={s.body}>{result.notice}</Text>
          </Card>
          <Card>
            <Text style={s.badge}>03 · 다음 상담 준비</Text>
            <Text style={s.body}>
              사건의 경과를 시간순으로 정리하고, 보유 자료와 확인하고 싶은
              질문을 모아 보세요.
            </Text>
            <Text style={s.small}>
              모든 분야에 공통으로 제공하는 자료 정리 안내입니다.
            </Text>
          </Card>
          <Card>
            <Text style={s.badge}>04 · 해야 할 일</Text>
            {todoLabels.map((t, i) => (
              <Check
                key={t}
                label={t}
                value={d.checks[i]}
                onChange={() =>
                  update((a) => ({
                    ...a,
                    draft: {
                      ...a.draft,
                      checks: a.draft.checks.map((v, j) => (j === i ? !v : v)),
                    },
                  }))
                }
              />
            ))}
          </Card>
          <Card>
            <Text style={s.badge}>05 · 도움받을 곳</Text>
            <Text style={s.body}>
              전문 상담 기관 안내는 실제 서비스 연동 시 제공됩니다.
            </Text>
          </Card>
        </>
      )}
    </Screen>
  );
}
export function Save() {
  const { data, update } = useApp(),
    d = data.draft,
    previous = data.cases.find((c) => c.id === d.caseId),
    [title, setTitle] = useState(previous?.title || `${d.category} 관련 상담`),
    [memo, setMemo] = useState(previous?.memo || ""),
    [deadline, setDeadline] = useState(previous?.deadline || ""),
    [keep, setKeep] = useState([true, true, true]),
    [error, setError] = useState("");
  function save() {
    if (!title.trim()) {
      setError("사건 제목을 입력해 주세요.");
      return;
    }
    if (deadline && !validDate(deadline)) {
      setError("기한을 실제 날짜로 입력해 주세요. (YYYY-MM-DD)");
      return;
    }
    const item = makeCase(
      d,
      {
        title,
        memo,
        deadline,
        keepResult: keep[0],
        keepEvidence: keep[1],
        keepTodos: keep[2],
      },
      previous,
    );
    update((a) => ({
      ...a,
      draft: emptyDraft(),
      cases: previous
        ? a.cases.map((c) => (c.id === item.id ? item : c))
        : [item, ...a.cases],
    }));
    router.dismissAll();
    router.replace("/(tabs)/cases");
  }
  return (
    <Screen
      footer={
        <Button
          label={previous ? "변경 내용 저장" : "사건 저장하기"}
          onPress={save}
        />
      }
    >
      <Heading
        title="나만의 기록으로 남겨요"
        sub="다음에 쉽게 찾을 수 있도록 이름을 붙여 주세요."
      />
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
        keyboardType="numbers-and-punctuation"
      />
      <Field
        label="메모 (선택)"
        value={memo}
        onChangeText={setMemo}
        multiline
        maxLength={1000}
      />
      <Card>
        <Text style={s.h2}>저장할 항목</Text>
        {[
          "상황 정리와 추가 질문 답변",
          "첨부자료 목록 (원본 제외)",
          "해야 할 일과 체크 상태",
        ].map((t, i) => (
          <Check
            key={t}
            label={t}
            value={keep[i]}
            onChange={() => setKeep((a) => a.map((v, j) => (j === i ? !v : v)))}
          />
        ))}
      </Card>
      {error ? <Text style={s.error}>{error}</Text> : null}
      <Notice>
        기기 내부 저장입니다. 앱 삭제나 데이터 초기화 시 기록이 사라질 수
        있습니다. 서버 계정과 동기화되지 않습니다.
      </Notice>
    </Screen>
  );
}
