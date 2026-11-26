import test from "node:test";
import assert from "node:assert/strict";
import { formatJudgmentDate } from "../src/domain/model.ts";
import { confirmOpenSource, isWebUrl, openWebSource, suggestionNavigation, webSourceHostNote } from "../src/services/officialSource.ts";
import { makeCase, resultForCase, wasWebSearchAnswer } from "../src/domain/model.ts";
import { suggestionDocument } from "../src/components/suggestionDocument.ts";

const precedent = (id) => ({
  id, title: `${id}에 관한 판례`, caseNumber: "2020고단1", court: "대법원", judgmentDate: "20201113",
  summary: "판례가 있습니다.", sourceUrl: `https://www.law.go.kr/LSW/precInfoP.do?precSeq=${id}`,
});
test("원문 링크는 확인 창에서 '열기'를 눌러야 열린다", async () => {
  const alerts = [];
  const opened = [];
  const url = precedent("233925").sourceUrl;
  confirmOpenSource(url, (...args) => alerts.push(args), async (u) => opened.push(u));
  assert.equal(alerts.length, 1);
  const [title, , buttons] = alerts[0];
  assert.equal(title, "외부 페이지 열기");
  assert.deepEqual(opened, []);
  buttons.find((b) => b.text === "취소").onPress?.();
  assert.deepEqual(opened, []);
  buttons.find((b) => b.text === "열기").onPress();
  assert.deepEqual(opened, [url]);
});

test("원문을 열지 못하면 실패 안내를 띄운다", async () => {
  const alerts = [];
  confirmOpenSource(precedent("1").sourceUrl, (...args) => alerts.push(args), () => Promise.reject(Error("x")));
  alerts[0][2].find((b) => b.text === "열기").onPress();
  await new Promise((resolve) => setImmediate(resolve));
  assert.equal(alerts[1][0], "열기 실패");
});

test("공식 출처가 아닌 주소는 열지 않고 이유를 알린다", () => {
  const alerts = [];
  const opened = [];
  confirmOpenSource("https://example.com/x", (...args) => alerts.push(args), async (u) => opened.push(u));
  assert.equal(alerts.length, 1);
  assert.equal(alerts[0][2], undefined);
  assert.match(alerts[0][1], /공식 출처/);
  assert.deepEqual(opened, []);
});

test("웹 검색 출처는 확인 창 없이 바로 열고, 검증에 실패하면 열지 않는다", () => {
  const alerts = [];
  const opened = [];
  openWebSource("https://example.go.kr/guide", (...args) => alerts.push(args), async (u) => opened.push(u));
  assert.deepEqual(alerts, []);
  assert.deepEqual(opened, ["https://example.go.kr/guide"]);
  openWebSource("https://law.go.kr@evil.example/x", (...args) => alerts.push(args), async (u) => opened.push(u));
  assert.equal(alerts[0][0], "열 수 없는 주소예요");
  assert.equal(alerts[0][2], undefined);
  assert.equal(opened.length, 1);
});

test("웹 검색 출처 URL 검증은 서버와 같은 규칙을 쓴다", () => {
  assert.equal(isWebUrl("https://example.go.kr/a"), true);
  assert.equal(isWebUrl("HTTPS://Example.go.kr/a"), true);
  for (const bad of ["https://", "http://example.com", "https://law.go.kr@evil.example/x", "https://user:pw@example.com", "javascript:alert(1)", 123, null])
    assert.equal(isWebUrl(bad), false, String(bad));
});

test("웹 출처 목록에 실제 이동할 도메인을 보여 준다", () => {
  assert.match(webSourceHostNote("vertexaisearch.cloud.google.com"), /최종 목적지는 열어 봐야 확인됩니다/);
  const idn = new URL("https://정부.한국/안내").hostname;
  assert.match(webSourceHostNote(idn), /도메인: xn--.*punycode/);
  assert.equal(webSourceHostNote("example.go.kr"), "도메인: example.go.kr");
});

test("Search Suggestions 안에서는 처음 그리기만 허용하고 링크는 외부로, 나머지는 막는다", () => {
  assert.equal(suggestionNavigation("about:blank"), "load");
  assert.equal(suggestionNavigation("https://www.google.com/search?q=x"), "external");
  assert.equal(suggestionNavigation("http://example.com"), "block");
  assert.equal(suggestionNavigation("javascript:alert(1)"), "block");
  assert.equal(suggestionNavigation("intent://x"), "block");
  const html = '<div class="chip"><a href="https://www.google.com/search?q=x">x</a></div>';
  assert.ok(suggestionDocument(html).includes(html));
  assert.ok(suggestionDocument(html, "_blank").includes('<base target="_blank">'));
});

test("사건 기록에는 웹 검색 답변 텍스트만 저장한다", () => {
  const web = {
    mode: "rag", summary: "웹 검색 안내", precedents: [], notice: "판례 근거 없음",
    sources: [{ title: "a", url: "https://a.example" }], searchSuggestionsHtml: "<div>제안</div>",
  };
  const draft = {
    category: "기타", date: "2026-01-01", amount: "", description: "상황", answers: [], evidence: [],
    checks: [false, false, false], result: web,
  };
  const saved = makeCase(draft, { title: "t", memo: "", deadline: "", keepResult: true, keepEvidence: true, keepTodos: true });
  assert.equal(saved.result.summary, "웹 검색 안내");
  assert.equal("sources" in saved.result, false);
  assert.equal("searchSuggestionsHtml" in saved.result, false);
  assert.equal(saved.result.webSourcesOmitted, true);
  assert.equal(wasWebSearchAnswer(saved.result), true);
  assert.equal(web.sources.length, 1, "원래 결과는 바꾸지 않는다");
  // 예전에 sources 와 함께 저장된 기록도 웹 검색 답변으로 알아본다(링크는 화면에 그리지 않음).
  assert.equal(wasWebSearchAnswer({ ...web, searchSuggestionsHtml: undefined }), true);
  const plain = { mode: "rag", summary: "일반 안내", precedents: [], notice: "x" };
  assert.deepEqual(resultForCase(plain), plain);
  assert.equal(wasWebSearchAnswer(plain), false);
});

test("판결일은 선고일자(yyyymmdd)를 점 형식으로 보여 준다", () => {
  assert.equal(formatJudgmentDate("20201113"), "2020.11.13");
  assert.equal(formatJudgmentDate("2020-01-01"), "2020-01-01");
});
