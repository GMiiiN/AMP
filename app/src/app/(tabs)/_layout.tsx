import React from "react";
import { Tabs } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { C } from "../../components/ui";
export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: C.green,
        tabBarInactiveTintColor: "#95A18C",
        tabBarStyle: { backgroundColor: "white", borderTopColor: C.line },
        tabBarLabelStyle: { fontSize: 11 },
        headerStyle: { backgroundColor: C.bg },
        headerShadowVisible: false,
        headerTintColor: C.green,
        headerTitleStyle: { fontSize: 19, fontWeight: "700" },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: "생활법률",
          tabBarLabel: "홈",
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="home-outline" color={color} size={size} />
          ),
        }}
      />
      <Tabs.Screen
        name="cases"
        options={{
          title: "내 사건",
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="folder-outline" color={color} size={size} />
          ),
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: "마이페이지",
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="person-outline" color={color} size={size} />
          ),
        }}
      />
    </Tabs>
  );
}
