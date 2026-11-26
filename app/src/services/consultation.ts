import { isOfficialSource, isWebUrl } from "./officialSource";
import {
  Draft,
  questions,
  ConsultationResult,
  QuestionMode,
} from "../domain/model";
export type { ConsultationResult } from "../domain/model";
export const usesApi = process.env.EXPO_PUBLIC_USE_API === "true";
export type QuestionSet = { questions: string[]; mode: QuestionMode };
export interface ConsultationService {
  getQuestions(draft: Draft): Promise<QuestionSet>;
  getResult(draft: Draft): Promise<ConsultationResult>;
}
export const demoConsultation: ConsultationService = {
  async getQuestions(draft) {
    return { questions: questions(draft.category), mode: "template" };
  },
  async getResult(draft) {
    return {
      mode: "demo",
      summary: draft.description,
      precedents: [],
      notice:
        draft.category === "기타"
          ? "기타 분야는 판례 검색 대상에서 제외됩니다."
          : "판례 검색은 서버에서 합니다. 서버 없이 앱만 실행한 데모에서는 판례가 나오지 않습니다.",
    };
  },
};
/** 화면에 그대로 보여 줄 수 있는 문구를 담은 오류. */
export class ConsultationError extends Error {}
export function requestBody(draft: Draft) {
  return {
    category: draft.category,
    date: draft.date,
    amount: draft.amount,
    description: draft.description,
    answers: draft.answers,
    // 생성 질문은 서버가 기억하지 않으므로, 받은 질문을 함께 보내 답과 짝짓게 한다.
    ...(draft.questions?.length === 3 ? { questions: draft.questions } : {}),
  };
}
async function post(path: string, draft: Draft) {
  const base = (process.env.EXPO_PUBLIC_API_URL || "").replace(/\/$/, "");
  if (!/^https?:\/\//.test(base))
    throw new ConsultationError("API 주소를 설정해 주세요.");
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 60000);
  let response: Response;
  try {
    response = await fetch(base + path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(requestBody(draft)),
      signal: controller.signal,
    });
  } catch {
    clearTimeout(timer);
    throw new ConsultationError(
      controller.signal.aborted
        ? "응답이 너무 늦어요. 잠시 후 다시 시도해 주세요."
        : "서버에 연결하지 못했어요. 네트워크와 서버 주소를 확인해 주세요.",
    );
  }
  try {
    const payload = await response.json().catch(() => null);
    if (!response.ok)
      throw new ConsultationError(
        typeof payload?.error?.message === "string"
          ? payload.error.message
          : "서버 요청에 실패했어요. 잠시 후 다시 시도해 주세요.",
      );
    if (!payload) throw new ConsultationError("서버 응답을 읽지 못했어요.");
    return payload;
  } finally {
    clearTimeout(timer);
  }
}
/** 오류를 화면 문구로 바꾼다. 형식 검증 실패 등은 기본 문구를 쓴다. */
export function errorMessage(e: unknown, fallback: string) {
  return e instanceof ConsultationError ? e.message : fallback;
}
const apiConsultation: ConsultationService = {
  async getQuestions(draft) {
    const r = await post("/api/consultations/questions", draft);
    if (
      !Array.isArray(r.questions) ||
      r.questions.length !== 3 ||
      r.questions.some((x: unknown) => typeof x !== "string" || !x.trim()) ||
      !["generated", "template"].includes(r.mode)
    )
      throw Error("질문 응답 형식이 올바르지 않습니다.");
    return { questions: r.questions, mode: r.mode };
  },
  async getResult(draft) {
    const r = await post("/api/consultations/result", draft);
    if (
      !["demo", "retrieval", "rag"].includes(r.mode) ||
      typeof r.summary !== "string" ||
      typeof r.notice !== "string" ||
      !Array.isArray(r.precedents) ||
      (r.searchMethod !== undefined &&
        !["embedding", "tfidf"].includes(r.searchMethod))
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
        (p.cited !== undefined && typeof p.cited !== "boolean") ||
        !isOfficialSource(p.sourceUrl)
      )
        throw Error("판례 출처 형식을 확인하지 못했습니다.");
    }
    if (
      r.sources !== undefined &&
      (!Array.isArray(r.sources) ||
        r.sources.some(
          (x: { title?: unknown; url?: unknown } | null) =>
            typeof x?.title !== "string" || !isWebUrl(x?.url),
        ))
    )
      throw Error("웹 검색 출처 형식을 확인하지 못했습니다.");
    if (r.searchSuggestionsHtml != null && typeof r.searchSuggestionsHtml !== "string")
      throw Error("검색 제안 형식을 확인하지 못했습니다.");
    return r;
  },
};
export const consultationService = usesApi ? apiConsultation : demoConsultation;
