import React from "react";
import { Stack } from "expo-router";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { StatusBar } from "expo-status-bar";
import { AppProvider } from "../state/AppProvider";
import { C } from "../components/ui";
export default function RootLayout() {
  return (
    <SafeAreaProvider>
      <AppProvider>
        <StatusBar style="dark" />
        <Stack
          screenOptions={{
            headerStyle: { backgroundColor: C.bg },
            headerTintColor: C.green,
            headerShadowVisible: false,
            headerTitleStyle: { fontSize: 16 },
            contentStyle: { backgroundColor: C.bg },
            headerBackTitle: "뒤로",
          }}
        >
          <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
          <Stack.Screen name="categories" options={{ title: "상담 분야" }} />
          <Stack.Screen name="situation" options={{ title: "상황 입력" }} />
          <Stack.Screen name="questions" options={{ title: "추가 질문" }} />
          <Stack.Screen name="result" options={{ title: "상담 결과" }} />
          <Stack.Screen name="save" options={{ title: "사건 저장" }} />
          <Stack.Screen name="case-detail" options={{ title: "사건 상세" }} />
          <Stack.Screen name="login" options={{ title: "로그인" }} />
          <Stack.Screen name="signup" options={{ title: "회원가입" }} />
        </Stack>
      </AppProvider>
    </SafeAreaProvider>
  );
}
