export function isOfficialSource(value: string) {
  try {
    const url = new URL(value);
    return (
      url.protocol === "https:" &&
      ["www.law.go.kr", "law.go.kr"].includes(url.hostname)
    );
  } catch {
    return false;
  }
}
type AlertButton = { text: string; style?: "cancel"; onPress?: () => void };
/** 판례 원문(국가법령정보센터)을 열기 전에 확인 창을 띄운다. 공식 출처가 아니면 열지 않는다. */
export function confirmOpenSource(
  url: string,
  alert: (title: string, message?: string, buttons?: AlertButton[]) => void,
  openURL: (url: string) => Promise<unknown>,
) {
  if (!isOfficialSource(url))
    return alert("열 수 없는 주소예요", "공식 출처(국가법령정보센터)가 아니라 열 수 없습니다.");
  alert("외부 페이지 열기", "국가법령정보센터 원문 페이지로 이동합니다.", [
    { text: "취소", style: "cancel" },
    {
      text: "열기",
      onPress: () =>
        void openURL(url).catch(() =>
          alert("열기 실패", "인터넷 연결을 확인해 주세요."),
        ),
    },
  ]);
}
