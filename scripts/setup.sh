#!/usr/bin/env bash
# 생활법률(AMP) 개발 환경 준비 스크립트 (macOS, bash 3.2 이상. Linux 에서도 대부분 동작).
# Windows 는 scripts/setup.ps1 을 쓰세요.
#
# 저장소 루트를 기준으로 동작하므로 어느 폴더에서 실행해도 됩니다.
#   1) server/.env, app/.env 가 없을 때만 각 .env.example 에서 복사 (이미 있으면 절대 덮어쓰지 않음)
#   2) app/.env 의 EXPO_PUBLIC_API_URL 한 줄만 http://<Mac IPv4>:8000 (또는 --api-url 값)으로 변경
#   3) server/.venv 생성 + pip install -r requirements.txt   (--skip-server 로 건너뜀)
#   4) app 폴더에서 npm ci                                    (--skip-app 으로 건너뜀)
#   5) scripts/check_env.py 로 환경 점검                       (--skip-check 로 건너뜀)
# 비밀 값(server/.env 의 GEMINI_API_KEY)은 만들지 않습니다. 팀장에게 받은 .env 를 server/.env 에 두세요(README.md).
# 판례 DB(data/vector_db/precedents.sqlite3)는 저장소에 포함되어 있습니다.
#
# 사용 예
#   bash scripts/setup.sh
#   bash scripts/setup.sh --skip-server --skip-app --api-url https://xxxx.trycloudflare.com
#
# 옵션
#   --api-url URL    자동 탐지 대신 app/.env 에 넣을 API 주소
#   --keep-api-url   app/.env 의 EXPO_PUBLIC_API_URL 을 바꾸지 않음(다른 팀원 서버 주소를 유지할 때)
#   --port N         자동 탐지 주소에 붙일 서버 포트 (기본 8000)
#   --python PATH    server/.venv 를 만들 Python 3.11 이상 (기본: python3.12 > python3.13 > python3.11 > python3 순서로 찾음)
#   --skip-server    server venv 생성과 pip install 건너뜀
#   --skip-app       app 의 npm ci 건너뜀
#   --skip-check     마지막 환경 점검 건너뜀
set -euo pipefail

API_URL=""
KEEP_API_URL=0
PORT=8000
PYTHON_BIN=""
SKIP_SERVER=0
SKIP_APP=0
SKIP_CHECK=0

if [ -t 1 ]; then
  C_STEP=$'\033[36m'; C_OK=$'\033[32m'; C_WARN=$'\033[33m'; C_FAIL=$'\033[31m'; C_END=$'\033[0m'
else
  C_STEP=""; C_OK=""; C_WARN=""; C_FAIL=""; C_END=""
fi
step() { printf '\n%s==> %s%s\n' "$C_STEP" "$1" "$C_END"; }
ok()   { printf '  %s[OK]%s   %s\n' "$C_OK" "$C_END" "$1"; }
info() { printf '  [INFO] %s\n' "$1"; }
warn() { printf '  %s[WARN]%s %s\n' "$C_WARN" "$C_END" "$1"; }
die()  { printf '\n%s[실패]%s %s\n' "$C_FAIL" "$C_END" "$1" >&2; exit 1; }

usage() { sed -n '2,24p' "$0" | sed 's/^# \{0,1\}//'; }

while [ $# -gt 0 ]; do
  case "$1" in
    --api-url) [ $# -ge 2 ] || die "--api-url 뒤에 주소를 적으세요."; API_URL="$2"; shift 2 ;;
    --api-url=*) API_URL="${1#*=}"; shift ;;
    --keep-api-url) KEEP_API_URL=1; shift ;;
    --port) [ $# -ge 2 ] || die "--port 뒤에 번호를 적으세요."; PORT="$2"; shift 2 ;;
    --port=*) PORT="${1#*=}"; shift ;;
    --python) [ $# -ge 2 ] || die "--python 뒤에 경로를 적으세요."; PYTHON_BIN="$2"; shift 2 ;;
    --python=*) PYTHON_BIN="${1#*=}"; shift ;;
    --skip-server) SKIP_SERVER=1; shift ;;
    --skip-app) SKIP_APP=1; shift ;;
    --skip-check) SKIP_CHECK=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "알 수 없는 옵션: $1 (도움말: bash scripts/setup.sh --help)" ;;
  esac
done

case "$PORT" in
  ''|*[!0-9]*) die "--port 는 숫자여야 합니다: $PORT" ;;
esac
if [ "$KEEP_API_URL" = 1 ] && [ -n "$API_URL" ]; then
  die "--api-url 과 --keep-api-url 은 함께 쓸 수 없습니다."
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SERVER_DIR="$REPO_ROOT/server"
APP_DIR="$REPO_ROOT/app"
[ -f "$SERVER_DIR/requirements.txt" ] && [ -f "$APP_DIR/package.json" ] \
  || die "저장소 루트를 찾지 못했습니다: $REPO_ROOT (scripts 폴더를 옮기지 마세요)"

# venv 안의 python 경로 (macOS/Linux: bin/python, Windows Git Bash: Scripts/python.exe)
venv_python() {
  if [ -x "$SERVER_DIR/.venv/bin/python" ]; then
    echo "$SERVER_DIR/.venv/bin/python"
  elif [ -f "$SERVER_DIR/.venv/Scripts/python.exe" ]; then
    echo "$SERVER_DIR/.venv/Scripts/python.exe"
  else
    return 1
  fi
}

python_version() { "$1" -c 'import sys; print(".".join(map(str, sys.version_info[:3])))' 2>/dev/null; }
python_ok() { "$1" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' >/dev/null 2>&1; }

# server/.venv 를 만들 Python 3.11 이상을 찾는다. 3.12 를 먼저 찾는다(권장 버전).
find_server_python() {
  local candidate found
  if [ -n "$PYTHON_BIN" ]; then
    python_ok "$PYTHON_BIN" || { echo "--python $PYTHON_BIN: 실행되지 않거나 Python 3.11 미만입니다." >&2; return 1; }
    echo "$PYTHON_BIN"; return 0
  fi
  for candidate in python3.12 python3.13 python3.11 python3 python; do
    if command -v "$candidate" >/dev/null 2>&1 && python_ok "$candidate"; then
      command -v "$candidate"; return 0
    fi
  done
  if command -v uv >/dev/null 2>&1; then
    found="$(uv python find '>=3.11' 2>/dev/null || true)"
    if [ -n "$found" ] && python_ok "$found"; then echo "$found"; return 0; fi
  fi
  echo "Python 3.11 이상(3.12 권장)을 찾지 못했습니다. brew install python@3.12 또는 https://www.python.org/downloads/ 로 설치하거나 --python 으로 지정하세요." >&2
  return 1
}

# Wi-Fi/이더넷 IPv4. macOS: 기본 경로 인터페이스(en*) > en0 > en1 순서로 ipconfig getifaddr.
# VPN(utun*) 같은 가상 인터페이스와 169.254.x.x(APIPA)는 뺀다. 결과: "IP 인터페이스"
detect_ip() {
  local iface ip default_iface
  if [ "$(uname -s)" = "Darwin" ]; then
    default_iface="$(route -n get default 2>/dev/null | awk '/interface:/ {print $2; exit}')"
    for iface in $default_iface en0 en1 en2; do
      case "$iface" in en*) ;; *) continue ;; esac
      ip="$(ipconfig getifaddr "$iface" 2>/dev/null || true)"
      case "$ip" in ''|169.254.*|127.*) continue ;; esac
      echo "$ip $iface"; return 0
    done
    return 1
  fi
  if command -v ip >/dev/null 2>&1; then  # Linux
    ip="$(ip -4 route get 1.1.1.1 2>/dev/null | awk '{for (i = 1; i < NF; i++) if ($i == "src") {print $(i + 1); exit}}')"
    iface="$(ip -4 route get 1.1.1.1 2>/dev/null | awk '{for (i = 1; i < NF; i++) if ($i == "dev") {print $(i + 1); exit}}')"
    case "$ip" in ''|169.254.*|127.*) return 1 ;; esac
    echo "$ip ${iface:-?}"; return 0
  fi
  return 1
}

# KEY=... 줄만 바꾸고 나머지 줄은 그대로 둔다(CRLF 줄은 CRLF 유지). 키가 없으면 끝에 추가한다.
# 결과: changed / unchanged
set_env_value() {
  local file="$1" key="$2" value="$3" tmp
  tmp="$(mktemp "${file}.XXXXXX")"
  # BINMODE=3: Windows Git Bash 의 gawk 가 CRLF 의 \r 을 지우지 않게 한다(macOS/Linux awk 에서는 영향 없음).
  ENV_KEY="$key" ENV_VALUE="$value" awk -v BINMODE=3 '
    BEGIN { key = ENVIRON["ENV_KEY"]; value = ENVIRON["ENV_VALUE"]; found = 0; lastcr = "" }
    {
      line = $0; cr = ""
      if (sub(/\r$/, "", line)) cr = "\r"
      lastcr = cr
      probe = line
      sub(/^[ \t]*/, "", probe)
      sub(/^export[ \t]+/, "", probe)
      if (index(probe, key) == 1 && substr(probe, length(key) + 1) ~ /^[ \t]*=/) {
        print key "=" value cr; found = 1; next
      }
      print $0
    }
    END { if (!found) print key "=" value lastcr }
  ' "$file" > "$tmp"
  if cmp -s "$tmp" "$file"; then
    rm -f "$tmp"; echo unchanged
  else
    cat "$tmp" > "$file"; rm -f "$tmp"; echo changed   # cat > 로 써서 원래 파일 권한을 유지
  fi
}

copy_env() {  # $1 대상, $2 예시, $3 표시 이름
  if [ -e "$1" ]; then
    info "$3 이미 있음 -> 그대로 둡니다(덮어쓰지 않음)"; return 0
  fi
  if [ ! -f "$2" ]; then
    warn "$3.example 이 없어 $3 을 만들지 못했습니다. git checkout -- $3.example 로 되살린 뒤 다시 실행하세요."; return 0
  fi
  cp "$2" "$1"
  ok "$3 생성 ($3.example 복사)"
}

update_api_url() {
  local app_env="$APP_DIR/.env" target detected result
  if [ "$KEEP_API_URL" = 1 ]; then info "EXPO_PUBLIC_API_URL 유지 (--keep-api-url)"; return 0; fi
  if [ ! -f "$app_env" ]; then warn "app/.env 가 없어 API 주소를 설정하지 못했습니다."; return 0; fi
  if [ -n "$API_URL" ]; then
    target="${API_URL%/}"
    case "$target" in
      http://?*|https://?*) ;;
      *) die "--api-url 형식이 틀렸습니다: $API_URL (예: http://192.168.0.31:8000, https://xxxx.trycloudflare.com)" ;;
    esac
    case "$target" in *[[:space:]]*) die "--api-url 에 공백이 있습니다: $API_URL" ;; esac
    info "--api-url 지정: $target"
  else
    if ! detected="$(detect_ip)"; then
      warn "Wi-Fi/이더넷 IPv4 를 찾지 못해 EXPO_PUBLIC_API_URL 을 그대로 둡니다. --api-url 로 직접 지정하세요."
      return 0
    fi
    target="http://${detected%% *}:$PORT"
    info "탐지한 IPv4: ${detected%% *} (인터페이스 ${detected#* })"
  fi
  result="$(set_env_value "$app_env" EXPO_PUBLIC_API_URL "$target")"
  if [ "$result" = changed ]; then
    ok "app/.env EXPO_PUBLIC_API_URL=$target (다른 줄은 그대로)"
  else
    ok "app/.env EXPO_PUBLIC_API_URL 이미 $target (변경 없음)"
  fi
}

install_server() {
  local py version vpy
  if vpy="$(venv_python)"; then
    python_ok "$vpy" || die "server/.venv 가 Python 3.11 미만이거나 손상되었습니다. server/.venv 폴더를 지운 뒤 다시 실행하세요."
    info "기존 server/.venv 사용 (Python $(python_version "$vpy"))"
  else
    py="$(find_server_python)" || die "Python 3.11 이상을 찾지 못했습니다."
    version="$(python_version "$py")"
    info "Python $version 로 server/.venv 생성: $py"
    "$py" -m venv "$SERVER_DIR/.venv" || die "venv 생성 실패"
    vpy="$(venv_python)" || die "venv 를 만들었지만 python 실행 파일이 없습니다."
  fi
  if ! "$vpy" -m pip --version >/dev/null 2>&1; then  # uv 등으로 만든 venv 에는 pip 이 없을 수 있다
    info "venv 에 pip 이 없어 ensurepip 으로 설치합니다."
    "$vpy" -m ensurepip --upgrade || die "ensurepip 실패"
  fi
  "$vpy" -m pip install --disable-pip-version-check -r "$SERVER_DIR/requirements.txt" || die "pip install 실패"
  ok "server 의존성 설치 완료"
}

install_app() {
  local node_version major minor
  command -v node >/dev/null 2>&1 || die "Node.js 를 찾지 못했습니다. Node.js 22.13 이상(LTS)을 설치하세요."
  command -v npm >/dev/null 2>&1 || die "npm 을 찾지 못했습니다. Node.js 를 다시 설치하세요."
  node_version="$(node -p 'process.versions.node')"
  major="${node_version%%.*}"; minor="${node_version#*.}"; minor="${minor%%.*}"
  if [ "$major" -lt 22 ] || { [ "$major" -eq 22 ] && [ "$minor" -lt 13 ]; }; then
    warn "Node.js v$node_version 입니다. 22.13 이상을 권장합니다."
  else
    info "Node.js v$node_version"
  fi
  (cd "$APP_DIR" && npm ci --no-audit --no-fund) || die "npm ci 실패"
  ok "app 의존성 설치 완료 (npm ci)"
}

run_check() {
  local py="" candidate
  if py="$(venv_python)"; then :; else
    py=""
    for candidate in python3 python; do
      if command -v "$candidate" >/dev/null 2>&1 \
         && "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' >/dev/null 2>&1; then
        py="$candidate"; break
      fi
    done
  fi
  if [ -z "$py" ]; then warn "Python 을 찾지 못해 점검을 건너뜁니다."; return 0; fi
  PYTHONIOENCODING=utf-8 "$py" "$REPO_ROOT/scripts/check_env.py"
}

echo "생활법률 개발 환경 준비 (저장소: $REPO_ROOT)"

step "1/5 환경 파일 (.env)"
copy_env "$SERVER_DIR/.env" "$SERVER_DIR/.env.example" "server/.env"
copy_env "$APP_DIR/.env" "$APP_DIR/.env.example" "app/.env"

step "2/5 앱이 접속할 API 주소 (app/.env 의 EXPO_PUBLIC_API_URL)"
update_api_url

step "3/5 서버 Python 환경 (server/.venv)"
if [ "$SKIP_SERVER" = 1 ]; then info "건너뜀 (--skip-server)"; else install_server; fi

step "4/5 앱 패키지 (npm ci)"
if [ "$SKIP_APP" = 1 ]; then info "건너뜀 (--skip-app)"; else install_app; fi

step "5/5 환경 점검 (scripts/check_env.py)"
check_code=0
if [ "$SKIP_CHECK" = 1 ]; then
  info "건너뜀 (--skip-check)"
else
  run_check || check_code=$?
fi

step "다음 단계"
echo "  서버(새 터미널): cd server && .venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
echo "  서버 응답 확인 : server/.venv/bin/python scripts/check_env.py --health"
echo "  앱(새 터미널)  : cd app && npx expo start --clear"
echo "  다른 팀원 서버에 붙기: bash scripts/setup.sh --skip-server --skip-app --api-url http://<그 PC IPv4>:8000"
echo "  다시 실행할 때 지금 주소를 유지하려면 --keep-api-url"
if [ "$check_code" -ne 0 ]; then
  printf '\n%s점검에서 실패 항목이 있습니다. 위 [FAIL] 줄을 확인하세요.%s\n' "$C_WARN" "$C_END"
  exit 1
fi
