export const categories = [
  {
    name: "중고사기",
    icon: "cube-outline",
    description: "거래와 물품 대금 문제",
    question: "거래 약속과 입금 내역이 남아 있나요?",
  },
  {
    name: "전세사기",
    icon: "home-outline",
    description: "보증금과 임대차 문제",
    question: "임대차 계약서를 가지고 있나요?",
  },
  {
    name: "소음공해",
    icon: "volume-high-outline",
    description: "이웃 간 소음 문제",
    question: "소음이 발생한 날짜와 시간을 기록했나요?",
  },
  {
    name: "교통사고",
    icon: "car-outline",
    description: "사고와 피해 상황",
    question: "사고 당시 사진이나 영상이 있나요?",
  },
  {
    name: "보이스피싱",
    icon: "call-outline",
    description: "의심스러운 연락과 피해",
    question: "상대방에게 돈이나 정보를 전달했나요?",
  },
  {
    name: "폭행",
    icon: "shield-outline",
    description: "신체적 피해와 다툼",
    question: "피해 상황을 확인할 자료가 있나요?",
  },
  {
    name: "임금체불",
    icon: "wallet-outline",
    description: "급여와 퇴직금 문제",
    question: "약속한 급여와 지급일을 확인할 수 있나요?",
  },
  {
    name: "명예훼손",
    icon: "chatbox-outline",
    description: "말과 글로 인한 피해",
    question: "문제가 된 게시물이나 발언 기록이 있나요?",
  },
  {
    name: "상속",
    icon: "people-outline",
    description: "가족과 재산 문제",
    question: "가족관계와 재산 정보를 확인했나요?",
  },
  {
    name: "기타",
    icon: "ellipsis-horizontal",
    description: "분류하기 어려운 고민",
    question: "상황을 확인할 수 있는 자료가 있나요?",
  },
] as const;
export type Category = (typeof categories)[number]["name"];
export type Evidence = {
  id: string;
  name: string;
  size: number;
  mimeType: string;
};
export type Precedent = {
  id: string;
  title: string;
  caseNumber: string;
  court: string;
  judgmentDate: string;
  summary: string;
  sourceUrl: string;
};
export type ConsultationResult = {
  mode: "demo" | "retrieval" | "rag";
  summary: string;
  precedents: Precedent[];
  notice: string;
};
export type Draft = {
  result?: ConsultationResult;
  caseId?: string;
  category: Category | "";
  date: string;
  amount: string;
  description: string;
  answers: string[];
  evidence: Evidence[];
  checks: boolean[];
};
export type CaseRecord = Draft & {
  id: string;
  title: string;
  memo: string;
  deadline: string;
  status: "진행 중" | "완료";
  createdAt: string;
  updatedAt: string;
  history: { at: string; label: string }[];
};
export type Profile = { name: string; email: string };
export type AppData = {
  version: 1;
  profile: Profile | null;
  draft: Draft;
  cases: CaseRecord[];
};
export const todoLabels = [
  "날짜와 사실관계 정리하기",
  "관련 대화와 자료 목록 만들기",
  "전문 상담에서 확인할 질문 준비하기",
];
export const emptyDraft = (): Draft => ({
  category: "",
  date: "",
  amount: "",
  description: "",
  answers: [],
  evidence: [],
  checks: [false, false, false],
});
export const initialData = (): AppData => ({
  version: 1,
  profile: null,
  draft: emptyDraft(),
  cases: [],
});
export function localDate(date = new Date()) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}
export function validDate(s: string) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(s)) return false;
  const [y, m, d] = s.split("-").map(Number);
  const date = new Date(y, m - 1, d);
  return (
    date.getFullYear() === y &&
    date.getMonth() === m - 1 &&
    date.getDate() === d
  );
}
export function validateDraft(d: Draft) {
  if (!categories.some((c) => c.name === d.category))
    return "상담 분야를 선택해 주세요.";
  if (!validDate(d.date) || d.date > localDate())
    return "발생일을 오늘 이전의 실제 날짜로 입력해 주세요. (YYYY-MM-DD)";
  if (d.amount && (!/^\d+$/.test(d.amount) || Number(d.amount) > 999999999999))
    return "금액은 0 이상 999,999,999,999원 이하의 정수로 입력해 주세요.";
  if (!d.description.trim() || d.description.length > 1000)
    return "상황을 1~1,000자로 입력해 주세요.";
  return "";
}
export function questions(category: string) {
  return [
    categories.find((c) => c.name === category)?.question ||
      "확인할 자료가 있나요?",
    "상대방에게 상황을 알리거나 대화를 시도했나요?",
    "지금 가장 먼저 정리하고 싶은 것은 무엇인가요?",
  ];
}
export function makeCase(
  draft: Draft,
  options: {
    title: string;
    memo: string;
    deadline: string;
    keepResult: boolean;
    keepEvidence: boolean;
    keepTodos: boolean;
  },
  previous?: CaseRecord,
): CaseRecord {
  const now = new Date().toISOString();
  return {
    ...draft,
    caseId: undefined,
    id:
      previous?.id ||
      `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`,
    title: options.title.trim(),
    memo: options.memo,
    deadline: options.deadline,
    status: previous?.status || "진행 중",
    createdAt: previous?.createdAt || now,
    updatedAt: now,
    result: options.keepResult ? draft.result : undefined,
    description: options.keepResult ? draft.description : "",
    answers: options.keepResult ? [...draft.answers] : [],
    evidence: options.keepEvidence ? [...draft.evidence] : [],
    checks: options.keepTodos ? [...draft.checks] : [false, false, false],
    history: [
      ...(previous?.history || []),
      { at: now, label: previous ? "상담 내용 갱신" : "사건 저장" },
    ],
  };
}
export function validateAccount(
  name: string,
  email: string,
  password: string,
  repeat: string,
  consents: boolean[],
) {
  if (!name.trim()) return "이름을 입력해 주세요.";
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim()))
    return "이메일 형식을 확인해 주세요.";
  if (password.length < 8) return "비밀번호는 8자 이상 입력해 주세요.";
  if (password !== repeat) return "비밀번호가 서로 일치하지 않습니다.";
  if (!consents.every(Boolean)) return "필수 약관에 모두 동의해 주세요.";
  return "";
}
