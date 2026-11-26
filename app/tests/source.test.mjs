import test from "node:test";
import assert from "node:assert/strict";
import { formatJudgmentDate } from "../src/domain/model.ts";
import { confirmOpenSource } from "../src/services/officialSource.ts";

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

test("공식 출처가 아닌 주소는 확인 창도 띄우지 않는다", () => {
  const alerts = [];
  confirmOpenSource("https://example.com/x", (...args) => alerts.push(args), async () => {});
  assert.equal(alerts.length, 0);
});

test("판결일은 선고일자(yyyymmdd)를 점 형식으로 보여 준다", () => {
  assert.equal(formatJudgmentDate("20201113"), "2020.11.13");
  assert.equal(formatJudgmentDate("2020-01-01"), "2020-01-01");
});
