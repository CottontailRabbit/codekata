#!/usr/bin/env python3
"""
Code Kata - 하루 시작 코딩 연습 프로그램
Python / Rust / C++ 1~2줄 카타를 반복 연습합니다.
Claude API로 무한 문제 생성 지원.
"""

import json
import random
import os
import sys
import re
from datetime import date
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
HISTORY_FILE = DATA_DIR / "history.json"
ENV_FILE = Path(__file__).parent / ".env"

# ─── 인증 ────────────────────────────────────────────────────

_cached_api_key = None


def get_api_key():
    """API 키를 환경변수 또는 .env에서 읽습니다."""
    global _cached_api_key
    if _cached_api_key:
        return _cached_api_key
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if key:
        _cached_api_key = key
        return key
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            if line.startswith("ANTHROPIC_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"').strip("'")
                if key:
                    _cached_api_key = key
                    return key
    return ""


def get_client():
    """인증된 Anthropic 클라이언트를 반환합니다."""
    try:
        import anthropic
    except ImportError:
        return None
    key = get_api_key()
    if not key:
        return None
    return anthropic.Anthropic(api_key=key)


def auth_status_str():
    """현재 인증 상태를 문자열로 반환."""
    if get_api_key():
        return f"{C.GREEN}ON{C.RESET}"
    return f"{C.RED}OFF{C.RESET}"


def setup_auth():
    """API 키 설정 화면"""
    clear()
    key = get_api_key()

    print(f"\n  {C.CYAN}{C.BOLD}── API 키 설정 ──{C.RESET}\n")
    print(f"  {C.DIM}https://console.anthropic.com/settings/keys 에서 발급{C.RESET}\n")

    if key:
        masked = key[:10] + "..." + key[-4:]
        print(f"  {C.GREEN}현재 키:{C.RESET} {masked}\n")

    try:
        new_key = input(f"  {C.CYAN}API 키>{C.RESET} ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return

    if not new_key:
        return

    # .env에 저장
    DATA_DIR.mkdir(exist_ok=True)
    if ENV_FILE.exists():
        lines = ENV_FILE.read_text().splitlines()
        new_lines = [l for l in lines if not l.startswith("ANTHROPIC_API_KEY=")]
        new_lines.append(f"ANTHROPIC_API_KEY={new_key}")
        ENV_FILE.write_text("\n".join(new_lines) + "\n")
    else:
        ENV_FILE.write_text(f"ANTHROPIC_API_KEY={new_key}\n")

    gitignore = Path(__file__).parent / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text(".env\n")
    elif ".env" not in gitignore.read_text():
        gitignore.write_text(gitignore.read_text().rstrip() + "\n.env\n")

    global _cached_api_key
    _cached_api_key = new_key
    os.environ["ANTHROPIC_API_KEY"] = new_key
    print(f"\n  {C.GREEN}API 키 저장 완료!{C.RESET}")
    input(f"  {C.DIM}Enter로 계속...{C.RESET}")


def generate_kata_with_ai(lang, history):
    """Claude API로 새로운 카타 문제를 생성합니다."""
    client = get_client()
    if not client:
        return None

    lang_label = {"python": "Python", "rust": "Rust", "cpp": "C++"}[lang]

    # 이전에 푼 문제 제목 수집 (중복 방지)
    solved_titles = []
    ai_history = history.get("ai_katas", {}).get(lang, [])
    for k in ai_history[-20:]:  # 최근 20개만
        solved_titles.append(k.get("title", ""))

    avoid = ""
    if solved_titles:
        avoid = f"\n이미 출제된 문제 (중복 피할 것): {', '.join(solved_titles)}"

    prompt = f"""당신은 {lang_label} 코딩 카타 출제자입니다.
1~2줄로 작성할 수 있는 짧은 코딩 연습 문제 1개를 만들어 주세요.

규칙:
- 문제는 반드시 1~2줄 코드로 풀 수 있어야 합니다
- 초급~중급 수준
- 구체적인 입력값과 기대 결과를 명시하세요
- 힌트는 핵심 함수/문법만 간결하게
{avoid}

반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트 없이 JSON만:
{{
  "title": "문제 제목 (짧게)",
  "desc": "문제 설명 (구체적 입력/출력 포함)",
  "hint": "핵심 힌트 (함수명이나 문법)",
  "answer": "모범 답안 코드 (1~2줄)",
  "check_contains": ["정답에 반드시 포함되어야 할 키워드1", "키워드2"]
}}"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text.strip()
        # JSON 블록 추출
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        kata_data = json.loads(text)

        # 검증용 함수 생성
        keywords = kata_data.get("check_contains", [])

        kata = {
            "id": f"ai_{lang}_{random.randint(10000, 99999)}",
            "title": kata_data["title"],
            "desc": kata_data["desc"],
            "hint": kata_data["hint"],
            "answer": [kata_data["answer"]],
            "check_contains": keywords,
            "ai_generated": True,
        }
        return kata

    except Exception as e:
        print(f"\n  {C.RED}AI 문제 생성 실패: {e}{C.RESET}")
        return None


# ─── 기본 문제 은행 (fallback) ────────────────────────────────

KATAS = {
    "python": [
        {
            "id": "py01", "title": "리스트 합계",
            "desc": "리스트 [1, 2, 3, 4, 5]의 합을 구하세요.",
            "hint": "sum() 내장 함수",
            "answer": ["sum([1, 2, 3, 4, 5])"],
            "check": lambda code: eval(code) == 15,
        },
        {
            "id": "py02", "title": "문자열 뒤집기",
            "desc": "문자열 'hello'를 뒤집으세요.",
            "hint": "슬라이싱 [::-1]",
            "answer": ["'hello'[::-1]"],
            "check": lambda code: eval(code) == "olleh",
        },
        {
            "id": "py03", "title": "짝수 필터",
            "desc": "[1,2,3,4,5,6]에서 짝수만 필터링하세요. (리스트 컴프리헨션)",
            "hint": "[x for x in ... if x % 2 == 0]",
            "answer": ["[x for x in [1,2,3,4,5,6] if x % 2 == 0]"],
            "check": lambda code: eval(code) == [2, 4, 6],
        },
        {
            "id": "py04", "title": "딕셔너리 생성",
            "desc": "keys=['a','b','c'], values=[1,2,3]으로 딕셔너리를 만드세요.",
            "hint": "dict(zip(keys, values))",
            "answer": ["dict(zip(['a','b','c'], [1,2,3]))"],
            "check": lambda code: eval(code) == {"a": 1, "b": 2, "c": 3},
        },
        {
            "id": "py05", "title": "최댓값 인덱스",
            "desc": "[10, 30, 20]에서 최댓값의 인덱스를 구하세요.",
            "hint": ".index(max(...))",
            "answer": ["[10, 30, 20].index(max([10, 30, 20]))"],
            "check": lambda code: eval(code) == 1,
        },
        {
            "id": "py06", "title": "문자열 반복",
            "desc": "'ha'를 3번 반복한 문자열을 만드세요.",
            "hint": "문자열 * 정수",
            "answer": ["'ha' * 3"],
            "check": lambda code: eval(code) == "hahaha",
        },
        {
            "id": "py07", "title": "리스트 평탄화",
            "desc": "[[1,2],[3,4],[5]]를 [1,2,3,4,5]로 평탄화하세요.",
            "hint": "이중 for 리스트 컴프리헨션",
            "answer": ["[x for sub in [[1,2],[3,4],[5]] for x in sub]"],
            "check": lambda code: eval(code) == [1, 2, 3, 4, 5],
        },
        {
            "id": "py08", "title": "집합 교집합",
            "desc": "{1,2,3}과 {2,3,4}의 교집합을 구하세요.",
            "hint": "& 연산자",
            "answer": ["{1,2,3} & {2,3,4}"],
            "check": lambda code: eval(code) == {2, 3},
        },
        {
            "id": "py09", "title": "enumerate 사용",
            "desc": "['a','b','c']를 enumerate로 [(0,'a'),(1,'b'),(2,'c')]로 변환하세요.",
            "hint": "list(enumerate(...))",
            "answer": ["list(enumerate(['a','b','c']))"],
            "check": lambda code: eval(code) == [(0, "a"), (1, "b"), (2, "c")],
        },
        {
            "id": "py10", "title": "lambda 정렬",
            "desc": "[('b',2),('a',1),('c',3)]을 두 번째 요소 기준으로 정렬하세요.",
            "hint": "sorted(..., key=lambda x: x[1])",
            "answer": ["sorted([('b',2),('a',1),('c',3)], key=lambda x: x[1])"],
            "check": lambda code: eval(code) == [("a", 1), ("b", 2), ("c", 3)],
        },
        {
            "id": "py11", "title": "map 사용",
            "desc": "[1,2,3]의 각 요소를 제곱한 리스트를 map으로 만드세요.",
            "hint": "list(map(lambda x: x**2, ...))",
            "answer": ["list(map(lambda x: x**2, [1,2,3]))"],
            "check": lambda code: eval(code) == [1, 4, 9],
        },
        {
            "id": "py12", "title": "딕셔너리 컴프리헨션",
            "desc": "{x: x**2 for x in range(5)}를 작성하세요.",
            "hint": "딕셔너리 컴프리헨션",
            "answer": ["{x: x**2 for x in range(5)}"],
            "check": lambda code: eval(code) == {0: 0, 1: 1, 2: 4, 3: 9, 4: 16},
        },
    ],
    "rust": [
        {
            "id": "rs01", "title": "변수 선언",
            "desc": "불변 변수 x에 정수 5를 바인딩하세요.",
            "hint": "let 키워드",
            "answer": ["let x = 5;"],
            "check": lambda code: re.search(r"let\s+x\s*(:\s*i32\s*)?=\s*5\s*;", code) is not None,
        },
        {
            "id": "rs02", "title": "가변 변수",
            "desc": "가변 변수 x에 5를 바인딩하세요.",
            "hint": "let mut",
            "answer": ["let mut x = 5;"],
            "check": lambda code: re.search(r"let\s+mut\s+x\s*(:\s*i32\s*)?=\s*5\s*;", code) is not None,
        },
        {
            "id": "rs03", "title": "벡터 생성",
            "desc": "1, 2, 3을 담은 벡터를 매크로로 생성하세요.",
            "hint": "vec![]",
            "answer": ["vec![1, 2, 3]"],
            "check": lambda code: "vec!" in code and "1" in code and "2" in code and "3" in code,
        },
        {
            "id": "rs04", "title": "String 생성",
            "desc": "\"hello\"로 String 타입을 생성하세요.",
            "hint": "String::from() 또는 .to_string()",
            "answer": ["String::from(\"hello\")"],
            "check": lambda code: 'String::from("hello")' in code or '"hello".to_string()' in code,
        },
        {
            "id": "rs05", "title": "Option 언래핑",
            "desc": "Some(5)에서 값을 unwrap하세요.",
            "hint": ".unwrap()",
            "answer": ["Some(5).unwrap()"],
            "check": lambda code: "Some(5)" in code and "unwrap()" in code,
        },
        {
            "id": "rs06", "title": "match 표현식",
            "desc": "x가 1이면 \"one\", _이면 \"other\"를 반환하는 match를 작성하세요.",
            "hint": "match x { 패턴 => 값 }",
            "answer": ["match x { 1 => \"one\", _ => \"other\" }"],
            "check": lambda code: "match" in code and "=>" in code,
        },
        {
            "id": "rs07", "title": "이터레이터 합계",
            "desc": "vec![1,2,3]의 이터레이터 합계를 구하세요.",
            "hint": ".iter().sum()",
            "answer": ["vec![1,2,3].iter().sum::<i32>()"],
            "check": lambda code: ".iter()" in code and "sum" in code,
        },
        {
            "id": "rs08", "title": "클로저",
            "desc": "x를 받아 x + 1을 반환하는 클로저를 만드세요.",
            "hint": "|파라미터| 본문",
            "answer": ["|x| x + 1"],
            "check": lambda code: "|x|" in code and "x + 1" in code,
        },
        {
            "id": "rs09", "title": "구조체 정의",
            "desc": "name: String 필드를 가진 Person 구조체를 정의하세요.",
            "hint": "struct 이름 { 필드: 타입 }",
            "answer": ["struct Person { name: String }"],
            "check": lambda code: "struct Person" in code and "name" in code and "String" in code,
        },
        {
            "id": "rs10", "title": "map 이터레이터",
            "desc": "vec![1,2,3]의 각 요소를 2배로 만든 벡터를 collect하세요.",
            "hint": ".iter().map(...).collect()",
            "answer": ["vec![1,2,3].iter().map(|x| x * 2).collect::<Vec<_>>()"],
            "check": lambda code: ".map(" in code and ".collect" in code and "* 2" in code,
        },
    ],
    "cpp": [
        {
            "id": "cp01", "title": "변수 선언",
            "desc": "int 타입 변수 x에 10을 초기화하세요.",
            "hint": "타입 이름 = 값;",
            "answer": ["int x = 10;"],
            "check": lambda code: re.search(r"int\s+x\s*[={]\s*10\s*[;}]", code) is not None,
        },
        {
            "id": "cp02", "title": "auto 타입 추론",
            "desc": "auto를 사용하여 변수 x에 3.14를 할당하세요.",
            "hint": "auto 키워드",
            "answer": ["auto x = 3.14;"],
            "check": lambda code: re.search(r"auto\s+x\s*=\s*3\.14\s*;", code) is not None,
        },
        {
            "id": "cp03", "title": "벡터 생성",
            "desc": "1, 2, 3을 담은 vector<int>를 초기화 리스트로 생성하세요.",
            "hint": "std::vector<int> v = {...};",
            "answer": ["std::vector<int> v = {1, 2, 3};"],
            "check": lambda code: "vector<int>" in code and "{1" in code,
        },
        {
            "id": "cp04", "title": "범위 기반 for",
            "desc": "벡터 v의 각 요소를 auto&로 순회하며 출력하는 for문을 작성하세요.",
            "hint": "for (auto& 변수 : 컨테이너)",
            "answer": ["for (auto& x : v) { std::cout << x; }"],
            "check": lambda code: "for" in code and "auto&" in code and ":" in code,
        },
        {
            "id": "cp05", "title": "람다 표현식",
            "desc": "int x를 받아 x * 2를 반환하는 람다를 만드세요.",
            "hint": "[캡처](파라미터) { return ... ; }",
            "answer": ["[](int x) { return x * 2; }"],
            "check": lambda code: "[]" in code and "return" in code and "x * 2" in code,
        },
        {
            "id": "cp06", "title": "스마트 포인터",
            "desc": "int 값 42를 가진 unique_ptr을 make_unique로 생성하세요.",
            "hint": "std::make_unique<타입>(값)",
            "answer": ["auto p = std::make_unique<int>(42);"],
            "check": lambda code: "make_unique<int>(42)" in code,
        },
        {
            "id": "cp07", "title": "string 생성",
            "desc": "std::string 변수 s에 \"hello\"를 할당하세요.",
            "hint": "std::string 변수 = \"값\";",
            "answer": ["std::string s = \"hello\";"],
            "check": lambda code: "string" in code and '"hello"' in code,
        },
        {
            "id": "cp08", "title": "const 참조",
            "desc": "const int& 타입으로 변수 x를 참조하는 ref를 선언하세요.",
            "hint": "const 타입& 이름 = 원본;",
            "answer": ["const int& ref = x;"],
            "check": lambda code: "const" in code and "int&" in code and "ref" in code,
        },
        {
            "id": "cp09", "title": "알고리즘 sort",
            "desc": "벡터 v를 std::sort로 정렬하세요.",
            "hint": "std::sort(시작, 끝);",
            "answer": ["std::sort(v.begin(), v.end());"],
            "check": lambda code: "sort(" in code and "v.begin()" in code and "v.end()" in code,
        },
        {
            "id": "cp10", "title": "transform",
            "desc": "v의 각 요소를 2배로 만들어 result에 넣는 std::transform를 작성하세요.",
            "hint": "std::transform(시작, 끝, 출력, 함수)",
            "answer": ["std::transform(v.begin(), v.end(), result.begin(), [](int x) { return x * 2; });"],
            "check": lambda code: "transform(" in code and "* 2" in code,
        },
    ],
}

# ─── 색상 ────────────────────────────────────────────────────

class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"


# ─── 히스토리 관리 ───────────────────────────────────────────

def load_history():
    if HISTORY_FILE.exists():
        return json.loads(HISTORY_FILE.read_text())
    return {"sessions": [], "solved": {}, "ai_katas": {}, "ai_solved_count": 0}


def save_history(history):
    DATA_DIR.mkdir(exist_ok=True)
    HISTORY_FILE.write_text(json.dumps(history, indent=2, ensure_ascii=False))


def get_streak(history):
    sessions = history.get("sessions", [])
    if not sessions:
        return 0
    sessions_sorted = sorted(set(sessions), reverse=True)
    streak = 0
    expected = date.today()
    for s in sessions_sorted:
        s_date = date.fromisoformat(s)
        if s_date == expected:
            streak += 1
            expected = date.fromordinal(expected.toordinal() - 1)
        elif s_date < expected:
            break
    return streak


# ─── UI 헬퍼 ─────────────────────────────────────────────────

def clear():
    os.system("clear" if os.name != "nt" else "cls")


def banner(history):
    streak = get_streak(history)
    total_static = sum(len(v) for v in history.get("solved", {}).values())
    total_ai = history.get("ai_solved_count", 0)
    total = total_static + total_ai
    today = date.today().isoformat()
    today_count = len([s for s in history.get("sessions", []) if s == today])
    print(f"""
{C.CYAN}{C.BOLD}  ┌─────────────────────────────────────────┐
  │         CODE KATA  카타 연습             │
  │      하루 시작, 손가락을 깨우자          │
  └─────────────────────────────────────────┘{C.RESET}

  {C.YELLOW}연속:{C.RESET} {streak}일  {C.DIM}|{C.RESET}  {C.YELLOW}오늘:{C.RESET} {today_count}문제  {C.DIM}|{C.RESET}  {C.YELLOW}누적:{C.RESET} {total}문제  {C.DIM}|{C.RESET}  {C.YELLOW}AI:{C.RESET} {auth_status_str()}
""")


def show_menu():
    print(f"  {C.BOLD}언어 선택{C.RESET}")
    print(f"  {C.BLUE}[1]{C.RESET} Python    {C.BLUE}[2]{C.RESET} Rust    {C.BLUE}[3]{C.RESET} C++")
    print()
    print(f"  {C.BOLD}모드{C.RESET}")
    print(f"  {C.MAGENTA}[a]{C.RESET} AI 무한 생성 (언어 선택 후)")
    print(f"  {C.BLUE}[r]{C.RESET} 랜덤      {C.BLUE}[s]{C.RESET} 통계    {C.BLUE}[k]{C.RESET} 인증설정  {C.BLUE}[q]{C.RESET} 종료")
    if not get_api_key():
        print(f"\n  {C.DIM}AI 모드: [k]로 API 키 설정 필요{C.RESET}")
    print()


def show_stats(history):
    clear()
    print(f"\n  {C.BOLD}{C.CYAN}── 통계 ──{C.RESET}\n")
    solved = history.get("solved", {})
    for lang in ["python", "rust", "cpp"]:
        total = len(KATAS[lang])
        done = len(solved.get(lang, []))
        bar_len = 20
        filled = int(bar_len * done / total) if total > 0 else 0
        bar = f"{'█' * filled}{'░' * (bar_len - filled)}"
        label = {"python": "Python", "rust": "Rust  ", "cpp": "C++   "}[lang]
        print(f"  {label}  {bar}  {done}/{total}")

    ai_count = history.get("ai_solved_count", 0)
    streak = get_streak(history)
    print(f"\n  {C.MAGENTA}AI 생성 문제 풀이:{C.RESET} {ai_count}개")
    print(f"  {C.YELLOW}연속 연습:{C.RESET} {streak}일")
    print(f"\n  {C.DIM}Enter로 돌아가기...{C.RESET}")
    input()


# ─── AI 채점 ─────────────────────────────────────────────────

def check_ai_answer(user_input, kata):
    """AI 생성 문제의 답을 채점합니다."""
    # 1. 키워드 포함 검사
    keywords = kata.get("check_contains", [])
    if keywords:
        matched = sum(1 for kw in keywords if kw in user_input)
        if matched >= len(keywords):
            return True

    # 2. Python이면 실행해서 비교 시도
    if kata["id"].startswith("ai_python"):
        try:
            user_result = eval(user_input)
            answer_result = eval(kata["answer"][0])
            if user_result == answer_result:
                return True
        except Exception:
            pass

    # 3. 정규화 후 문자열 비교
    def normalize(s):
        return re.sub(r'\s+', '', s).lower()

    if normalize(user_input) == normalize(kata["answer"][0]):
        return True

    return False


# ─── 카타 실행 (기본 모드) ───────────────────────────────────

def run_kata(lang, history):
    solved = history.get("solved", {}).get(lang, [])
    unsolved = [k for k in KATAS[lang] if k["id"] not in solved]

    if not unsolved:
        print(f"\n  {C.GREEN}모든 {lang} 기본 카타를 완료했습니다! 다시 풀어볼까요?{C.RESET}")
        history["solved"][lang] = []
        save_history(history)
        unsolved = KATAS[lang]

    kata = random.choice(unsolved)
    return _present_kata(lang, kata, history, ai_mode=False)


# ─── 카타 실행 (AI 모드) ────────────────────────────────────

def run_ai_kata(lang, history):
    lang_label = {"python": "Python", "rust": "Rust", "cpp": "C++"}[lang]
    lang_color = {"python": C.BLUE, "rust": C.RED, "cpp": C.MAGENTA}[lang]

    clear()
    print(f"\n  {C.MAGENTA}AI가 {lang_label} 문제를 생성하는 중...{C.RESET}\n")

    kata = generate_kata_with_ai(lang, history)
    if kata is None:
        print(f"  {C.RED}AI 문제 생성 실패.{C.RESET}")
        print(f"  {C.DIM}[k]로 API 키를 설정하세요.{C.RESET}")
        input(f"\n  {C.DIM}Enter로 돌아가기...{C.RESET}")
        return True

    return _present_kata(lang, kata, history, ai_mode=True)


# ─── 문제 출제 공통 ─────────────────────────────────────────

def _present_kata(lang, kata, history, ai_mode=False):
    lang_label = {"python": "Python", "rust": "Rust", "cpp": "C++"}[lang]
    lang_color = {"python": C.BLUE, "rust": C.RED, "cpp": C.MAGENTA}[lang]
    mode_tag = f" {C.MAGENTA}[AI]{C.RESET}" if ai_mode else ""

    clear()
    print(f"""
  {lang_color}{C.BOLD}── {lang_label} 카타 ──{C.RESET}{mode_tag}

  {C.BOLD}{kata['title']}{C.RESET}
  {kata['desc']}

  {C.DIM}힌트: {kata['hint']}{C.RESET}
""")

    attempts = 0
    while True:
        try:
            user_input = input(f"  {lang_color}>{C.RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return False

        if user_input.lower() in ("q", "quit", "skip"):
            print(f"\n  {C.YELLOW}건너뛰기{C.RESET}")
            return True

        if not user_input:
            continue

        attempts += 1

        # 채점
        if ai_mode:
            correct = check_ai_answer(user_input, kata)
        else:
            try:
                correct = kata["check"](user_input)
            except Exception:
                correct = False

        if correct:
            # 기록 저장
            if ai_mode:
                if lang not in history.get("ai_katas", {}):
                    history["ai_katas"][lang] = []
                history["ai_katas"][lang].append({
                    "title": kata["title"],
                    "desc": kata["desc"],
                })
                history["ai_solved_count"] = history.get("ai_solved_count", 0) + 1
            else:
                if lang not in history.get("solved", {}):
                    history["solved"][lang] = []
                if kata["id"] not in history["solved"][lang]:
                    history["solved"][lang].append(kata["id"])

            today = date.today().isoformat()
            history["sessions"].append(today)
            save_history(history)

            msg = "한 번에 성공!" if attempts == 1 else f"{attempts}번 만에 성공!"

            print(f"\n  {C.GREEN}{C.BOLD}  {msg}{C.RESET}")
            print(f"  {C.DIM}모범 답안: {kata['answer'][0]}{C.RESET}\n")
            input(f"  {C.DIM}Enter로 계속...{C.RESET}")
            return True
        else:
            print(f"  {C.RED}틀렸습니다. 다시 시도하세요.{C.RESET}")
            if attempts >= 3:
                print(f"  {C.DIM}정답 참고: {kata['answer'][0]}{C.RESET}")


# ─── 메인 루프 ───────────────────────────────────────────────

def main():
    history = load_history()
    lang_map = {"1": "python", "2": "rust", "3": "cpp"}

    while True:
        clear()
        banner(history)
        show_menu()

        try:
            choice = input(f"  {C.CYAN}선택>{C.RESET} ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print(f"\n\n  {C.CYAN}내일도 연습하세요!{C.RESET}\n")
            break

        if choice == "q":
            print(f"\n  {C.CYAN}내일도 연습하세요!{C.RESET}\n")
            break
        elif choice == "s":
            show_stats(history)
        elif choice == "k":
            setup_auth()
        elif choice == "r":
            lang = random.choice(["python", "rust", "cpp"])
            run_kata(lang, history)
        elif choice == "a":
            # AI 모드 - 언어 선택
            clear()
            print(f"\n  {C.MAGENTA}{C.BOLD}── AI 무한 생성 모드 ──{C.RESET}\n")
            print(f"  {C.BLUE}[1]{C.RESET} Python    {C.BLUE}[2]{C.RESET} Rust    {C.BLUE}[3]{C.RESET} C++\n")
            try:
                lang_choice = input(f"  {C.MAGENTA}언어>{C.RESET} ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                continue
            if lang_choice not in lang_map:
                continue
            lang = lang_map[lang_choice]

            # 연속 풀기
            while True:
                if not run_ai_kata(lang, history):
                    break
                try:
                    again = input(f"\n  {C.YELLOW}계속 풀기? (Enter=계속 / q=메뉴){C.RESET} ").strip().lower()
                except (EOFError, KeyboardInterrupt):
                    print()
                    break
                if again == "q":
                    break
        elif choice in lang_map:
            lang = lang_map[choice]
            # 연속 풀기 모드
            while True:
                if not run_kata(lang, history):
                    break
                try:
                    again = input(f"\n  {C.YELLOW}계속 풀기? (Enter=계속 / q=메뉴){C.RESET} ").strip().lower()
                except (EOFError, KeyboardInterrupt):
                    print()
                    break
                if again == "q":
                    break
        else:
            print(f"  {C.RED}잘못된 입력입니다.{C.RESET}")
            input()


if __name__ == "__main__":
    main()
