import { Draft, questions, ConsultationResult } from "../domain/model";
export type { ConsultationResult } from "../domain/model";
export const usesApi = process.env.EXPO_PUBLIC_USE_API === "true";
export interface ConsultationService {
  getQuestions(draft: Draft): Promise<string[]>;
  getResult(draft: Draft): Promise<ConsultationResult>;
}
export const demoConsultation: ConsultationService = {
  async getQuestions(draft) {
    return questions(draft.category);
  },
  async getResult(draft) {
    return {
      mode: "demo",
      summary: draft.description,
      precedents: [],
      notice:
        draft.category === "기타"
          ? "기타 분야는 판례 검색 대상에서 제외됩니다."
          : "판례 검색 API 연결 전이므로 확인된 근거 판례가 없습니다.",
    };
  },
};
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
async function post(path: string, draft: Draft) {
  const base = (process.env.EXPO_PUBLIC_API_URL || "").replace(/\/$/, "");
  if (!/^https?:\/\//.test(base)) throw Error("API 주소를 설정해 주세요.");
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 60000);
  try {
    const response = await fetch(base + path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        category: draft.category,
        date: draft.date,
        amount: draft.amount,
        description: draft.description,
        answers: draft.answers,
      }),
      signal: controller.signal,
    });
    const payload = await response.json();
    if (!response.ok)
      throw Error(
        typeof payload?.error?.message === "string"
          ? payload.error.message
          : "서버 요청에 실패했습니다.",
      );
    return payload;
  } finally {
    clearTimeout(timer);
  }
}
const apiConsultation: ConsultationService = {
  async getQuestions(draft) {
    const r = await post("/api/consultations/questions", draft);
    if (
      !Array.isArray(r.questions) ||
      r.questions.length !== 3 ||
      r.questions.some((x: unknown) => typeof x !== "string")
    )
      throw Error("질문 응답 형식이 올바르지 않습니다.");
    return r.questions;
  },
  async getResult(draft) {
    const r = await post("/api/consultations/result", draft);
    if (
      !["demo", "retrieval", "rag"].includes(r.mode) ||
      typeof r.summary !== "string" ||
      typeof r.notice !== "string" ||
      !Array.isArray(r.precedents)
    )
      throw Error("결과 응답 형식이 올바르지 않습니다.");
    for (const p of r.precedents) {
      if (
        ![
          "id",
          "title",
          "caseNumber",
          "court",
          "judgmentDate",
          "summary",
          "sourceUrl",
        ].every((k) => typeof p[k] === "string") ||
        !isOfficialSource(p.sourceUrl)
      )
        throw Error("판례 출처 형식을 확인하지 못했습니다.");
    }
    return r;
  },
};
export const consultationService = usesApi ? apiConsultation : demoConsultation;
