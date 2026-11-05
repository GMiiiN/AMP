import React, { useState } from "react";
import { Text, View, Pressable, Alert, Share } from "react-native";
import { router } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import {
  Screen,
  Heading,
  Button,
  Notice,
  Field,
  Card,
  Check,
  s,
  C,
} from "../components/ui";
import { useApp } from "../state/AppProvider";
import { validateAccount } from "../domain/model";
const terms = [
  {
    title: "이용약관",
    body: "현재는 모바일 앱의 화면과 동작을 검토하는 프론트엔드 체험판입니다. 실제 서버 계정이나 법률 서비스를 제공하지 않습니다. 정식 서비스의 약관은 운영 정책 확정 후 제공해야 합니다.",
  },
  {
    title: "개인정보 처리 안내",
    body: "사건, 작성 중인 내용과 프로필은 현재 기기에 저장됩니다. 원본 첨부파일은 저장하거나 전송하지 않습니다. 체험 비밀번호는 앱 실행 메모리에만 유지하며 기기 저장소에 기록하지 않습니다. 계정별 접근 제어 및 저장 암호화가 구현된 정식 서비스가 아니므로 실제 민감정보는 입력하지 마세요. 데이터 삭제 메뉴로 이 앱의 저장 기록을 제거할 수 있습니다.",
  },
  {
    title: "법률정보 이용 안내",
    body: "자료 정리는 법률 전문가의 자문이나 확정적 판단이 아닙니다. 실제 AI 및 판례 검색이 연결되지 않았으며 검증되지 않은 판례나 승소 확률을 제시하지 않습니다.",
  },
];
export function Auth({ signup = false }: { signup?: boolean }) {
  const { account, setAccount, update } = useApp(),
    [name, setName] = useState(""),
    [email, setEmail] = useState(""),
    [password, setPassword] = useState(""),
    [repeat, setRepeat] = useState(""),
    [consents, setConsents] = useState([false, false, false]),
    [error, setError] = useState("");
  function submit() {
    const mail = email.trim().toLowerCase();
    if (signup) {
      const msg = validateAccount(name, mail, password, repeat, consents);
      if (msg) {
        setError(msg);
        return;
      }
      setAccount({ name: name.trim(), email: mail, password });
      Alert.alert(
        "체험 계정 생성",
        "현재 앱 실행 중에만 로그인할 수 있어요. 앱을 완전히 종료하면 다시 가입해야 합니다.",
      );
      router.replace("/login");
    } else {
      if (!account || account.email !== mail || account.password !== password) {
        setError(
          "이메일 또는 비밀번호를 확인해 주세요. 현재 실행 중에 만든 체험 계정만 로그인할 수 있습니다.",
        );
        return;
      }
      update((d) => ({
        ...d,
        profile: { name: account.name, email: account.email },
      }));
      router.replace("/(tabs)");
    }
  }
  return (
    <Screen>
      <View style={{ alignItems: "center", marginVertical: 18 }}>
        <View
          style={[
            s.iconbox,
            {
              width: 62,
              height: 62,
              borderRadius: 20,
              backgroundColor: C.green,
            },
          ]}
        >
          <Ionicons name="scale-outline" size={32} color={C.lime} />
        </View>
      </View>
      <Heading
        kicker="생활법률"
        title={signup ? "내 법률 기록의 시작" : "다시 만나 반가워요"}
        sub={
          signup
            ? "간단한 정보로 체험 계정을 만들어 보세요."
            : "내 상황에 맞는 법률 길잡이"
        }
      />
      <Notice>
        화면 검토용 체험 계정입니다. 실제로 사용하는 비밀번호는 입력하지 마세요.
      </Notice>
      {signup ? (
        <Field
          label="이름"
          value={name}
          onChangeText={setName}
          maxLength={30}
        />
      ) : null}
      <Field
        label="이메일"
        value={email}
        onChangeText={setEmail}
        autoCapitalize="none"
        keyboardType="email-address"
        autoCorrect={false}
      />
      <Field
        label="비밀번호"
        value={password}
        onChangeText={setPassword}
        secureTextEntry
        autoCapitalize="none"
        placeholder="8자 이상"
        maxLength={128}
      />
      {signup ? (
        <>
          <Field
            label="비밀번호 확인"
            value={repeat}
            onChangeText={setRepeat}
            secureTextEntry
            maxLength={128}
          />
          {terms.map((t, i) => (
            <View key={t.title}>
              <Check
                label={`${i === 2 ? "법률 자문이 아님 확인" : t.title + " 동의"} (필수)`}
                value={consents[i]}
                onChange={() =>
                  setConsents((a) => a.map((v, j) => (i === j ? !v : v)))
                }
              />
              <Pressable onPress={() => Alert.alert(t.title, t.body)}>
                <Text style={[s.link, { textAlign: "right", paddingTop: 0 }]}>
                  내용 보기
                </Text>
              </Pressable>
            </View>
          ))}
        </>
      ) : null}
      {error ? (
        <Text accessibilityRole="alert" style={s.error}>
          {error}
        </Text>
      ) : null}
      <Button
        label={signup ? "가입하기" : "로그인"}
        onPress={submit}
        disabled={
          signup
            ? !name.trim() ||
              !email ||
              !password ||
              !repeat ||
              !consents.every(Boolean)
            : !email || !password
        }
      />
      <View style={[s.row, { marginVertical: 12 }]}>
        <Pressable
          onPress={() => router.replace(signup ? "/login" : "/signup")}
        >
          <Text style={s.link}>
            {signup ? "이미 계정이 있나요? 로그인" : "회원가입"}
          </Text>
        </Pressable>
        <Pressable
          onPress={() =>
            Alert.alert(
              "비밀번호 찾기",
              "서버 이메일 인증 연결 전입니다. 체험 계정은 앱을 다시 시작한 뒤 새로 만들 수 있습니다.",
            )
          }
        >
          <Text style={s.link}>비밀번호 찾기</Text>
        </Pressable>
      </View>
      {!signup ? (
        <View style={{ gap: 12 }}>
          <Button
            secondary
            label="카카오로 시작"
            onPress={() =>
              Alert.alert(
                "준비 중",
                "카카오 인증 서버는 아직 연결되지 않았습니다.",
              )
            }
          />
          <Button
            secondary
            label="Google로 시작"
            onPress={() =>
              Alert.alert(
                "준비 중",
                "Google 인증 서버는 아직 연결되지 않았습니다.",
              )
            }
          />
        </View>
      ) : null}
      <Pressable onPress={() => router.replace("/(tabs)")}>
        <Text style={[s.link, { textAlign: "center", marginTop: 16 }]}>
          로그인 없이 체험하기 →
        </Text>
      </Pressable>
    </Screen>
  );
}
export function Profile() {
  const { data, update, clear } = useApp(),
    [editing, setEditing] = useState(false),
    [name, setName] = useState(data.profile?.name || "");
  return (
    <Screen>
      <Heading title="마이페이지" sub="내 정보와 이 기기의 기록을 관리해요." />
      <Card>
        <View style={s.row}>
          <View
            style={[s.iconbox, { width: 52, height: 52, borderRadius: 26 }]}
          >
            <Ionicons name="person-outline" size={24} color={C.green} />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={s.h2}>{data.profile?.name || "방문자"}님</Text>
            <Text style={s.small}>
              {data.profile?.email || "로그인 없이 체험 중"}
            </Text>
          </View>
        </View>
        {data.profile ? (
          <Button
            secondary
            label="이름 수정"
            onPress={() => setEditing(!editing)}
          />
        ) : (
          <Button
            label="로그인 / 회원가입"
            onPress={() => router.push("/login")}
          />
        )}
        {editing ? (
          <>
            <Field
              label="이름"
              value={name}
              onChangeText={setName}
              maxLength={30}
            />
            <Button
              label="수정 저장"
              disabled={!name.trim()}
              onPress={() => {
                update((d) => ({
                  ...d,
                  profile: d.profile
                    ? { ...d.profile, name: name.trim() }
                    : null,
                }));
                setEditing(false);
              }}
            />
          </>
        ) : null}
      </Card>
      <Notice>
        저장한 사건 {data.cases.length}개 · 기기에 저장된 기록입니다. 계정별
        서버 동기화는 연결 전입니다.
      </Notice>
      <Card>
        <Pressable
          style={s.row}
          onPress={() => {
            void Share.share({
              title: "생활법률 기록",
              message: JSON.stringify(
                {
                  version: 1,
                  exportedAt: new Date().toISOString(),
                  cases: data.cases,
                },
                null,
                2,
              ),
            }).catch(() => Alert.alert("공유 실패", "다시 시도해 주세요."));
          }}
        >
          <Text style={s.body}>사건 기록 내보내기 (JSON 텍스트)</Text>
          <Ionicons name="share-outline" size={20} color={C.green} />
        </Pressable>
        <View style={s.divider} />
        <Pressable
          onPress={() =>
            Alert.alert(
              "알림 설정",
              "기한은 사건 상세에 표시됩니다. 푸시·이메일 알림은 서버 연결 후 제공됩니다.",
            )
          }
        >
          <Text style={s.body}>알림 설정</Text>
        </Pressable>
        {terms.map((t) => (
          <View key={t.title}>
            <View style={s.divider} />
            <Pressable onPress={() => Alert.alert(t.title, t.body)}>
              <Text style={s.body}>{t.title} →</Text>
            </Pressable>
          </View>
        ))}
      </Card>
      <Text style={[s.small, { marginBottom: 22, textAlign: "center" }]}>
        생활법률 MOBILE · 22S · v1.0
      </Text>
      {data.profile ? (
        <Button
          secondary
          label="로그아웃"
          onPress={() => {
            update((d) => ({ ...d, profile: null }));
            Alert.alert(
              "로그아웃",
              "이 기기의 사건 기록은 유지됩니다. 필요하면 체험 데이터 삭제를 이용해 주세요.",
            );
          }}
        />
      ) : null}
      <Pressable
        onPress={() =>
          Alert.alert(
            "모든 체험 데이터를 삭제할까요?",
            "프로필, 사건 및 작성 중인 내용을 삭제합니다. 되돌릴 수 없습니다.",
            [
              { text: "취소", style: "cancel" },
              {
                text: "모두 삭제",
                style: "destructive",
                onPress: () => {
                  void clear()
                    .then(() => router.replace("/(tabs)"))
                    .catch(() =>
                      Alert.alert(
                        "삭제 실패",
                        "데이터를 삭제하지 못했습니다. 다시 시도해 주세요.",
                      ),
                    );
                },
              },
            ],
          )
        }
      >
        <Text
          style={[
            s.link,
            { color: C.danger, textAlign: "center", marginTop: 18 },
          ]}
        >
          체험 계정 및 데이터 삭제
        </Text>
      </Pressable>
    </Screen>
  );
}
