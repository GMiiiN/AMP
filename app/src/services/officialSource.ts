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
/**
 * 기타 분야 웹 검색 출처 검증. 서버(normalize_web_url)와 같은 규칙:
 * https(대소문자 무시), 호스트 있음, 사용자 정보(user@host) 없음.
 */
export function webUrlHost(value: unknown) {
  if (typeof value !== "string") return null;
  try {
    const url = new URL(value.trim());
    const authority = value.trim().replace(/^[a-z]+:\/\//i, "").split(/[/?#]/)[0];
    if (url.protocol !== "https:" || !url.hostname || url.username || url.password || authority.includes("@"))
      return null;
    return url.hostname;
  } catch {
    return null;
  }
}
export function isWebUrl(value: unknown) {
  return webUrlHost(value) !== null;
}
/** Google 검색(grounding) 출처는 이 주소를 거쳐 실제 페이지로 이동한다. */
export const GROUNDING_REDIRECT_HOST = "vertexaisearch.cloud.google.com";
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
/** 웹 출처 도메인 안내 문구. 확인 창 대신 목록에 그대로 보여 준다(IDN 은 URL 이 punycode(xn--)로 바꿔 준다). */
export function webSourceHostNote(host: string) {
  const notes = [`도메인: ${host}`];
  if (host.split(".").some((label) => label.startsWith("xn--")))
    notes.push("국제화 도메인(punycode 표기)");
  if (host === GROUNDING_REDIRECT_HOST)
    notes.push("Google 검색을 거쳐 이동하며 최종 목적지는 열어 봐야 확인됩니다");
  return notes.join(" · ");
}
/**
 * 웹 검색 출처를 바로 연다. Gemini API 약관이 링크와 목적지 사이의 중간 화면을 금지하므로 확인 창을 두지 않는다.
 * 검증을 통과하지 못한 주소는 열지 않고 이유만 알린다.
 */
export function openWebSource(url: string, alert: AlertFn, openURL: OpenFn) {
  if (!isWebUrl(url))
    return alert("열 수 없는 주소예요", "안전한 웹 주소(https)가 아니라 열 수 없습니다.");
  void openURL(url).catch(() => alert("열기 실패", "인터넷 연결을 확인해 주세요."));
}
/** WebView 의 탐색 요청 중 판단에 쓰는 값(react-native-webview ShouldStartLoadRequest 의 일부). */
export type SuggestionRequest = { url: string; isTopFrame?: boolean; navigationType?: string };
/**
 * Search Suggestions(WebView) 안의 탐색 규칙.
 * - 처음 HTML 을 그리는 한 번(about:blank·data:)만 허용하고, 그 뒤의 about:blank·data: 는 막는다.
 * - 하위 프레임(isTopFrame=false)의 탐색은 외부로 열지 않고 막는다.
 * - iOS 는 사용자가 링크를 탭한 경우(navigationType="click")만 외부 브라우저로 연다.
 *   Android 는 navigationType 을 주지 않으므로 https 링크면 외부로 연다.
 * - 그 밖의 탐색은 모두 막는다.
 */
export function suggestionNavigation(
  request: SuggestionRequest,
  initialLoaded: boolean,
): "load" | "external" | "block" {
  const { url, isTopFrame, navigationType } = request;
  const initialDocument = url === "about:blank" || url.startsWith("data:");
  if (initialDocument) return !initialLoaded && isTopFrame !== false ? "load" : "block";
  if (isTopFrame === false) return "block";
  if (navigationType !== undefined && navigationType !== "click") return "block";
  return isWebUrl(url) ? "external" : "block";
}
