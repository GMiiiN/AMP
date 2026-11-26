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
/** 기타 분야 웹 검색 출처처럼 https 주소인지 확인한다. */
export function isWebUrl(value: unknown) {
  try {
    return typeof value === "string" && new URL(value).protocol === "https:";
  } catch {
    return false;
  }
}
type AlertButton = { text: string; style?: "cancel"; onPress?: () => void };
type AlertFn = (title: string, message?: string, buttons?: AlertButton[]) => void;
type OpenFn = (url: string) => Promise<unknown>;
function confirmThenOpen(url: string, message: string, alert: AlertFn, openURL: OpenFn) {
  alert("외부 페이지 열기", message, [
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
/** 판례 원문(국가법령정보센터)을 열기 전에 확인 창을 띄운다. 공식 출처가 아니면 열지 않는다. */
export function confirmOpenSource(url: string, alert: AlertFn, openURL: OpenFn) {
  if (!isOfficialSource(url))
    return alert("열 수 없는 주소예요", "공식 출처(국가법령정보센터)가 아니라 열 수 없습니다.");
  confirmThenOpen(url, "국가법령정보센터 원문 페이지로 이동합니다.", alert, openURL);
}
/** 웹 검색 출처를 열기 전에 확인 창을 띄운다. https 주소가 아니면 열지 않는다. */
export function confirmOpenWebSource(url: string, alert: AlertFn, openURL: OpenFn) {
  if (!isWebUrl(url))
    return alert("열 수 없는 주소예요", "안전한(https) 주소가 아니라 열 수 없습니다.");
  confirmThenOpen(url, "Google 검색으로 찾은 외부 웹페이지로 이동합니다. 내용은 직접 확인해 주세요.", alert, openURL);
}
