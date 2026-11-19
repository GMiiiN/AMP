import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { closest } from "../src/domain/matchPrecedent.ts";
const catalog = JSON.parse(readFileSync(new URL("../src/domain/precedentCatalog.json", import.meta.url)));
test("같은 분야에서도 상황과 표현에 따라 다른 판례를 반환", () => {
  const group = catalog["소음공해"];
  assert.equal(closest("윗집 소음 때문에 임대차 계약 해지를 요구했고 보증금을 반환받고 싶습니다", group)?.id, "601889");
  assert.equal(closest("대구비행장 인근 주민입니다. 항공기 소음 때문에 위자료를 청구하려고 합니다", group)?.id, "161161");
});
test("같은 분야라도 무관한 입력은 제외", () => {
  assert.equal(closest("노트북 배터리 교체", catalog["상속"]), undefined);
});

test("9개 분야 각각 10건이며 출처와 상세본문이 일치", () => {
  const details = JSON.parse(readFileSync(new URL("../src/domain/judgmentDetails.json", import.meta.url)));
  assert.equal(Object.keys(catalog).length, 9);
  const ids = new Set();
  for (const cases of Object.values(catalog)) {
    assert.equal(cases.length, 10);
    for (const item of cases) {
      assert.equal(new URL(item.sourceUrl).hostname, "www.law.go.kr");
      assert.equal(new URL(item.sourceUrl).searchParams.get("precSeq"), item.id);
      assert.equal(details[item.id].number, item.number);
      assert.ok(details[item.id].order.length && details[item.id].reasons.length);
      ids.add(item.id);
    }
  }
  assert.equal(ids.size, 90);
});
