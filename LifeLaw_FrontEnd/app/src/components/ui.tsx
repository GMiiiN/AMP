import React, { ReactNode } from "react";
import {
  View,
  Text,
  Pressable,
  TextInput,
  TextInputProps,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { useApp } from "../state/AppProvider";
export const C = {
  green: "#234A3C",
  lime: "#D8E8B8",
  bg: "#F6F7F2",
  text: "#263C32",
  muted: "#738072",
  line: "#DFE5D9",
  white: "#FFFFFF",
  danger: "#A34A3C",
};
export function Screen({
  children,
  footer,
}: {
  children: ReactNode;
  footer?: ReactNode;
}) {
  const { storageError, retry } = useApp();
  return (
    <SafeAreaView edges={["left", "right", "bottom"]} style={s.root}>
      <KeyboardAvoidingView
        style={s.root}
        behavior={Platform.OS === "ios" ? "padding" : undefined}
        keyboardVerticalOffset={92}
      >
        <ScrollView
          contentContainerStyle={s.content}
          keyboardShouldPersistTaps="handled"
          automaticallyAdjustKeyboardInsets
        >
          {storageError ? (
            <Pressable onPress={retry}>
              <Notice>{storageError} 탭하여 재시도</Notice>
            </Pressable>
          ) : null}
          {children}
        </ScrollView>
        {footer ? <View style={s.footer}>{footer}</View> : null}
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}
export function Heading({
  title,
  sub,
  kicker = "EVERYDAY LEGAL GUIDE",
}: {
  title: string;
  sub?: string;
  kicker?: string;
}) {
  return (
    <View style={{ marginBottom: 22 }}>
      <Text style={s.kicker}>{kicker}</Text>
      <Text accessibilityRole="header" style={s.h1}>
        {title}
      </Text>
      {sub ? <Text style={s.body}>{sub}</Text> : null}
    </View>
  );
}
export function Button({
  label,
  onPress,
  secondary = false,
  disabled = false,
  icon,
}: {
  label: string;
  onPress: () => void;
  secondary?: boolean;
  disabled?: boolean;
  icon?: React.ComponentProps<typeof Ionicons>["name"];
}) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ disabled }}
      disabled={disabled}
      onPress={onPress}
      style={({ pressed }) => [
        s.button,
        secondary && s.secondary,
        { opacity: disabled ? 0.4 : pressed ? 0.75 : 1 },
      ]}
    >
      <Text style={[s.buttonText, secondary && { color: C.green }]}>
        {label}
      </Text>
      {icon ? (
        <Ionicons name={icon} size={19} color={secondary ? C.green : C.white} />
      ) : null}
    </Pressable>
  );
}
export function Card({ children }: { children: ReactNode }) {
  return <View style={s.card}>{children}</View>;
}
export function Notice({ children }: { children: ReactNode }) {
  return (
    <View style={s.notice}>
      <Text style={s.noticeText}>{children}</Text>
    </View>
  );
}
export function Field({ label, ...props }: TextInputProps & { label: string }) {
  return (
    <View style={s.field}>
      <Text style={s.label}>{label}</Text>
      <TextInput
        accessibilityLabel={label}
        placeholderTextColor="#98A291"
        {...props}
        style={[
          s.input,
          props.multiline && { minHeight: 130, textAlignVertical: "top" },
          props.style,
        ]}
      />
    </View>
  );
}
export function Check({
  label,
  value,
  onChange,
}: {
  label: string;
  value: boolean;
  onChange: () => void;
}) {
  return (
    <Pressable
      accessibilityRole="checkbox"
      accessibilityState={{ checked: value }}
      onPress={onChange}
      style={s.check}
    >
      <Ionicons
        name={value ? "checkbox" : "square-outline"}
        color={value ? C.green : "#9BA88D"}
        size={25}
      />
      <Text style={[s.body, { flex: 1, color: C.text }]}>{label}</Text>
    </Pressable>
  );
}
export function Step({ current }: { current: number }) {
  return (
    <View style={s.steps}>
      {["상황 입력", "추가 질문", "상담 결과"].map((label, i) => (
        <View key={label} style={s.step}>
          <View style={[s.dot, i === current && { backgroundColor: C.green }]}>
            <Text
              style={{ color: i === current ? "white" : C.muted, fontSize: 12 }}
            >
              {i + 1}
            </Text>
          </View>
          <Text
            style={{ fontSize: 11, color: i === current ? C.green : C.muted }}
          >
            {label}
          </Text>
        </View>
      ))}
    </View>
  );
}
export function Section({
  title,
  children,
}: {
  title: string;
  children?: ReactNode;
}) {
  return (
    <View style={s.section}>
      <Text accessibilityRole="header" style={s.h2}>
        {title}
      </Text>
      {children}
    </View>
  );
}
export function Empty({
  text = "아직 저장한 사건이 없어요",
  sub = "상담 내용을 저장하면 이곳에서 다시 확인할 수 있어요.",
}: {
  text?: string;
  sub?: string;
}) {
  return (
    <View style={s.empty}>
      <Ionicons name="folder-open-outline" size={36} color="#8A9B78" />
      <Text style={s.h2}>{text}</Text>
      <Text style={[s.body, { textAlign: "center" }]}>{sub}</Text>
    </View>
  );
}
export const s = StyleSheet.create({
  root: { flex: 1, backgroundColor: C.bg },
  content: { padding: 22, paddingBottom: 32, gap: 0 },
  footer: {
    padding: 16,
    gap: 10,
    borderTopWidth: 1,
    borderColor: C.line,
    backgroundColor: C.white,
  },
  kicker: {
    fontSize: 10,
    letterSpacing: 1.7,
    color: "#879777",
    fontWeight: "600",
    marginBottom: 9,
  },
  h1: {
    fontSize: 27,
    lineHeight: 37,
    fontWeight: "700",
    letterSpacing: -1,
    color: C.text,
    marginBottom: 10,
  },
  h2: { fontSize: 18, fontWeight: "700", color: C.text, lineHeight: 27 },
  body: { fontSize: 14, lineHeight: 23, color: C.muted },
  small: { fontSize: 12, lineHeight: 19, color: C.muted },
  button: {
    minHeight: 52,
    borderRadius: 13,
    backgroundColor: C.green,
    alignItems: "center",
    justifyContent: "center",
    flexDirection: "row",
    gap: 10,
    padding: 14,
  },
  buttonText: { fontSize: 15, fontWeight: "700", color: "white" },
  secondary: { backgroundColor: C.white, borderWidth: 1, borderColor: C.line },
  card: {
    padding: 20,
    borderRadius: 18,
    backgroundColor: "white",
    borderWidth: 1,
    borderColor: C.line,
    marginBottom: 16,
    gap: 12,
  },
  notice: {
    padding: 14,
    borderRadius: 12,
    backgroundColor: "#EAF0DF",
    marginBottom: 18,
  },
  noticeText: { fontSize: 12, lineHeight: 20, color: "#62764E" },
  field: { marginBottom: 20, gap: 9 },
  label: { fontSize: 14, fontWeight: "600", color: C.text },
  input: {
    borderWidth: 1,
    borderColor: C.line,
    borderRadius: 11,
    paddingHorizontal: 14,
    paddingVertical: 14,
    fontSize: 15,
    color: C.text,
    backgroundColor: "white",
    minHeight: 50,
  },
  check: {
    flexDirection: "row",
    gap: 10,
    paddingVertical: 12,
    alignItems: "center",
    minHeight: 48,
  },
  steps: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 24,
  },
  step: { flexDirection: "row", gap: 7, alignItems: "center" },
  dot: {
    width: 25,
    height: 25,
    borderRadius: 13,
    backgroundColor: "#E4EBD9",
    alignItems: "center",
    justifyContent: "center",
  },
  section: {
    marginTop: 10,
    marginBottom: 15,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  empty: {
    padding: 28,
    gap: 13,
    alignItems: "center",
    backgroundColor: "white",
    borderRadius: 17,
    borderWidth: 1,
    borderStyle: "dashed",
    borderColor: C.line,
  },
  row: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 10,
  },
  chip: {
    paddingHorizontal: 12,
    paddingVertical: 9,
    borderRadius: 9,
    backgroundColor: "#EAF0DF",
  },
  error: { color: C.danger, fontSize: 13, lineHeight: 21, marginBottom: 14 },
  link: { color: C.green, fontSize: 13, paddingVertical: 12 },
  bar: {
    height: 5,
    backgroundColor: "#E6EDDC",
    borderRadius: 8,
    overflow: "hidden",
  },
  badge: { color: "#5D764B", fontSize: 11, fontWeight: "600" },
  hero: {
    backgroundColor: C.green,
    padding: 26,
    borderRadius: 22,
    marginBottom: 22,
    gap: 14,
  },
  grid: { flexDirection: "row", flexWrap: "wrap", gap: 12 },
  category: {
    width: "47.8%",
    backgroundColor: "white",
    borderWidth: 1,
    borderColor: C.line,
    padding: 18,
    borderRadius: 16,
    gap: 10,
    minHeight: 130,
  },
  iconbox: {
    width: 42,
    height: 42,
    borderRadius: 13,
    backgroundColor: "#EAF0DF",
    justifyContent: "center",
    alignItems: "center",
  },
  option: {
    minHeight: 54,
    borderWidth: 1,
    borderColor: C.line,
    padding: 15,
    borderRadius: 12,
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    marginBottom: 11,
    backgroundColor: "white",
  },
  selected: { borderColor: C.green, backgroundColor: "#EDF3E5" },
  divider: { borderTopWidth: 1, borderColor: C.line, marginVertical: 14 },
  tab: { paddingVertical: 12, paddingHorizontal: 17, borderRadius: 10 },
  tabSelected: { backgroundColor: C.green },
  timeline: {
    borderLeftWidth: 2,
    borderColor: "#CFDDBD",
    paddingLeft: 16,
    marginVertical: 10,
    gap: 15,
  },
});
