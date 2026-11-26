import test from "node:test";
import assert from "node:assert/strict";
import { formatJudgmentDate } from "../src/domain/model.ts";
import { confirmOpenSource, confirmOpenWebSource, isWebUrl } from "../src/services/officialSource.ts";

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

test("웹 검색 출처는 https 주소만 확인 창을 거쳐 연다", () => {
  const alerts = [];
  const opened = [];
  confirmOpenWebSource("https://example.go.kr/guide", (...args) => alerts.push(args), async (u) => opened.push(u));
  assert.equal(alerts[0][0], "외부 페이지 열기");
  assert.deepEqual(opened, []);
  alerts[0][2].find((b) => b.text === "열기").onPress();
  assert.deepEqual(opened, ["https://example.go.kr/guide"]);
  confirmOpenWebSource("http://example.com", (...args) => alerts.push(args), async (u) => opened.push(u));
  assert.equal(alerts[1][2], undefined);
  assert.equal(opened.length, 1);
});

test("웹 검색 출처 URL 검증은 서버와 같은 규칙을 쓴다", () => {
  assert.equal(isWebUrl("https://example.go.kr/a"), true);
  assert.equal(isWebUrl("HTTPS://Example.go.kr/a"), true);
  for (const bad of ["https://", "http://example.com", "https://law.go.kr@evil.example/x", "https://user:pw@example.com", "javascript:alert(1)", 123, null])
    assert.equal(isWebUrl(bad), false, String(bad));
});

test("웹 출처 확인 창은 실제 이동할 도메인을 보여 준다", () => {
  const alerts = [];
  const open = async () => {};
  confirmOpenWebSource("https://vertexaisearch.cloud.google.com/grounding-api-redirect/abc", (...args) => alerts.push(args), open);
  assert.match(alerts[0][1], /이동할 도메인: vertexaisearch\.cloud\.google\.com/);
  assert.match(alerts[0][1], /최종 목적지는 열어 봐야 확인됩니다/);
  confirmOpenWebSource("https://정부.한국/안내", (...args) => alerts.push(args), open);
  assert.match(alerts[1][1], /이동할 도메인: xn--/);
  assert.match(alerts[1][1], /punycode/);
  confirmOpenWebSource("https://law.go.kr@evil.example/x", (...args) => alerts.push(args), open);
  assert.equal(alerts[2][0], "열 수 없는 주소예요");
  assert.equal(alerts[2][2], undefined);
});

test("판결일은 선고일자(yyyymmdd)를 점 형식으로 보여 준다", () => {
  assert.equal(formatJudgmentDate("20201113"), "2020.11.13");
  assert.equal(formatJudgmentDate("2020-01-01"), "2020-01-01");
});
