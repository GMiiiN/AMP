import test from "node:test";
import assert from "node:assert/strict";
import {
  emptyDraft,
  validateDraft,
  validDate,
  makeCase,
  validateAccount,
} from "../src/domain/model.ts";
const good = () => ({
  ...emptyDraft(),
  category: "임금체불",
  date: "2026-01-01",
  amount: "20000",
  description: "급여 지급일이 지났습니다.",
  answers: ["네"],
  checks: [true, false, false],
});
test("rejects impossible/future dates and malformed amounts", () => {
  assert.equal(validDate("2025-02-29"), false);
  assert.equal(validDate("2024-02-29"), true);
  assert.equal(validateDraft(good()), "");
  assert.ok(validateDraft({ ...good(), date: "2999-01-01" }));
  assert.ok(validateDraft({ ...good(), amount: "-10" }));
  assert.ok(validateDraft({ ...good(), description: "  " }));
});
test("resuming a completed case preserves identity, status and history", () => {
  const d = good(),
    opts = {
      title: "급여 확인",
      memo: "메모",
      deadline: "",
      keepResult: true,
      keepEvidence: true,
      keepTodos: true,
    };
  const first = makeCase(d, opts);
  first.status = "완료";
  const next = makeCase({ ...d, description: "추가 정보" }, opts, first);
  assert.equal(next.id, first.id);
  assert.equal(next.status, "완료");
  assert.equal(next.createdAt, first.createdAt);
  assert.equal(next.history.length, 2);
  next.checks[0] = false;
  assert.equal(d.checks[0], true);
});
test("save options exclude confidential result and attachment fields", () => {
  const d = {
    ...good(),
    result: { mode: "demo", summary: "개인 내용", precedents: [], notice: "" },
    evidence: [
      { id: "a", name: "예시.pdf", size: 1, mimeType: "application/pdf" },
    ],
  };
  const c = makeCase(d, {
    title: "제목",
    memo: "",
    deadline: "",
    keepResult: false,
    keepEvidence: false,
    keepTodos: false,
  });
  assert.equal(c.description, "");
  assert.equal(c.result, undefined);
  assert.deepEqual(c.answers, []);
  assert.deepEqual(c.evidence, []);
  assert.deepEqual(c.checks, [false, false, false]);
});
test("account rejects missing consent and password mismatch", () => {
  assert.ok(
    validateAccount("사용자", "a@b.kr", "12345678", "12345678", [
      true,
      false,
      true,
    ]),
  );
  assert.ok(
    validateAccount("사용자", "a@b.kr", "12345678", "x", [true, true, true]),
  );
  assert.equal(
    validateAccount("사용자", "a@b.kr", "12345678", "12345678", [
      true,
      true,
      true,
    ]),
    "",
  );
});
