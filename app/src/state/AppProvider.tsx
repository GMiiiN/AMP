import React, {
  createContext,
  useContext,
  useEffect,
  useRef,
  useState,
  ReactNode,
} from "react";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { ActivityIndicator, View, Text, Pressable } from "react-native";
import { AppData, initialData, Profile } from "../domain/model";
const KEY = "@lifelaw/mobile/v1";
type Account = Profile & { password: string };
type Store = {
  data: AppData;
  update: (fn: (d: AppData) => AppData) => void;
  storageError: string;
  retry: () => void;
  account: Account | null;
  setAccount: React.Dispatch<React.SetStateAction<Account | null>>;
  clear: () => Promise<void>;
};
const Context = createContext<Store | null>(null);
export function AppProvider({ children }: { children: ReactNode }) {
  const [data, setData] = useState(initialData),
    [ready, setReady] = useState(false),
    [loadError, setLoadError] = useState(""),
    [storageError, setStorageError] = useState(""),
    [revision, setRevision] = useState(0),
    [account, setAccount] = useState<Account | null>(null);
  const queue = useRef(Promise.resolve());
  const [loadAttempt, setLoadAttempt] = useState(0);
  useEffect(() => {
    let active = true;
    AsyncStorage.getItem(KEY).then(raw => {
      const parsed = raw ? JSON.parse(raw) : initialData();
      if (parsed.version !== 1 || !Array.isArray(parsed.cases) ||
          !parsed.draft || !Array.isArray(parsed.draft.answers) ||
          !Array.isArray(parsed.draft.evidence) || !Array.isArray(parsed.draft.checks)) {
        throw Error("invalid stored data");
      }
      if (active) {setData(parsed);setLoadError("");setReady(true);}
    }).catch(() => {if (active) setLoadError("저장된 데이터를 읽지 못했습니다. 다시 시도해 주세요.");});
    return () => {active = false;};
  }, [loadAttempt]);
  useEffect(() => {
    if (!ready) return;
    const snapshot = JSON.stringify(data);
    queue.current = queue.current
      .catch(() => {})
      .then(async () => {
        try {
          await AsyncStorage.setItem(KEY, snapshot);
          setStorageError("");
        } catch {
          setStorageError(
            "기기 저장에 실패했습니다. 앱을 닫기 전에 저장을 다시 시도해 주세요.",
          );
        }
      });
  }, [data, ready, revision]);
  async function clear() {
    await queue.current.catch(() => {});
    await AsyncStorage.removeItem(KEY);
    setData(initialData());
    setAccount(null);
    setReady(true);
    setLoadError("");
  }
  if (!ready)
    return (
      <View
        style={{
          flex: 1,
          justifyContent: "center",
          alignItems: "center",
          padding: 28,
          gap: 20,
          backgroundColor: "#F6F7F2",
        }}
      >
        {loadError ? (
          <>
            <Text>{loadError}</Text>
            <Pressable onPress={() => setLoadAttempt(v => v + 1)}>
              <Text>다시 읽기</Text>
            </Pressable>
          </>
        ) : (
          <>
            <ActivityIndicator color="#234A3C" />
            <Text>기록을 불러오고 있어요</Text>
          </>
        )}
      </View>
    );
  return (
    <Context.Provider
      value={{
        data,
        update: setData,
        storageError,
        retry: () => setRevision((r) => r + 1),
        account,
        setAccount,
        clear,
      }}
    >
      {children}
    </Context.Provider>
  );
}
export function useApp() {
  const value = useContext(Context);
  if (!value) throw Error("AppProvider missing");
  return value;
}
