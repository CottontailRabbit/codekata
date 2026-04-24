---
name: kata
description: 하루 시작 코딩 연습. 타이핑 카타 + 객관식 코드 분석. Python/Rust/C++
trigger: /kata
---

# /kata

하루 시작 코딩 연습 스킬. 두 가지 유형의 문제를 출제합니다:
- **타이핑 카타**: 1~2줄 짧은 코드를 직접 타이핑 (3회 기회)
- **객관식 퀴즈**: 긴 코드를 읽고 분석하는 문제 (1회 기회)

## Usage

```
/kata              # 랜덤 언어, 랜덤 유형 1문제
/kata python       # Python 문제
/kata rust         # Rust 문제
/kata cpp          # C++ 문제
/kata go           # Go 문제
/kata js           # JavaScript 문제
/kata ts           # TypeScript 문제
/kata java         # Java 문제
/kata kotlin       # Kotlin 문제
/kata swift        # Swift 문제
/kata zig          # Zig 문제
/kata python 5     # Python 5문제 연속
/kata stats        # 통계 보기
```

## 지원 언어

python, rust, cpp, go, js (JavaScript), ts (TypeScript), java, kotlin, swift, zig

랜덤 모드(`/kata`)에서는 위 언어 중 하나를 랜덤으로 선택합니다.

## 두 가지 문제 유형

문제를 출제할 때 **타이핑**과 **객관식**을 랜덤으로 섞어서 출제합니다. 대략 반반 비율.

---

### 유형 A: 타이핑 카타 (기존)

1~2줄로 풀 수 있는 짧은 코딩 문제. 사용자가 직접 코드를 타이핑합니다.

**출제 형식:**
```
── Python 카타 [타이핑] ──

[문제 제목]
문제 설명 (구체적 입력값과 기대 결과 포함)

힌트: 핵심 함수명이나 문법
```

**규칙:**
- 1~2줄 코드로 풀 수 있는 문제
- 초급~중급 수준
- 3회 기회, 3회 틀리면 정답 공개
- 정답 판단 시 공백/세미콜론/따옴표 스타일 차이는 무시
- AskUserQuestion으로 답변 대기 (options에 skip/q 포함)

---

### 유형 B: 객관식 퀴즈 (신규)

5~20줄 정도의 코드를 보여주고 분석하는 문제. **1회 기회**만 있습니다.

**문제 카테고리** (랜덤 선택):
1. **출력 예측**: "이 코드의 출력은?" 
2. **버그 찾기**: "이 코드의 버그는?"
3. **빈칸 채우기**: "___에 들어갈 코드는?"
4. **시간복잡도**: "이 코드의 시간복잡도는?"
5. **동작 설명**: "이 코드가 하는 일은?"
6. **에러 예측**: "이 코드 실행 시 발생하는 에러는?"

**출제 형식:**
```
── Python 카타 [객관식] ──

[문제 제목]

다음 코드를 읽고 질문에 답하세요:

\```python
(5~20줄 코드)
\```

질문: (구체적 질문)
```

그 다음 AskUserQuestion을 호출하되, options에 4개 보기를 넣습니다.
- 4개 보기 중 1개만 정답
- 보기는 그럴듯한 오답(distractors)을 포함해야 함
- multiSelect: false
- **1회 기회** — 선택 즉시 정답/오답 판정

**정답일 때:**
```
정답! [정답 보기]

해설: (왜 이것이 정답인지 1~2줄 설명)
```

**오답일 때:**
```
오답! 정답은 [정답 보기]

해설: (왜 이것이 정답인지, 사용자가 고른 보기가 왜 틀린지 1~2줄 설명)
```

**객관식 문제 생성 규칙:**
- 코드는 실제로 동작하는 현실적인 코드여야 함
- 함정(tricky) 요소를 1~2개 포함 (연산자 우선순위, 스코프, 타입 변환, 소유권 등)
- 보기 순서를 매번 랜덤하게 섞기
- 정답 보기의 위치가 항상 같은 곳에 오지 않도록 주의

---

## 히스토리 관리

채점 결과를 `~/Desktop/deploy/codekata/data/kata_history.json`에 기록합니다.
이 파일은 GitHub 레포 `CottontailRabbit/codekata`의 `data/kata_history.json`에 추적/푸시됩니다.

```json
{
  "sessions": ["2026-04-20", "2026-04-20"],
  "solved": {
    "python": [{"title": "문제제목", "date": "2026-04-20", "attempts": 1, "type": "typing"}],
    "rust": [{"title": "문제제목", "date": "2026-04-20", "attempts": 1, "type": "quiz", "result": "correct"}],
    "cpp": []
  }
}
```

히스토리 파일이 없으면 새로 생성합니다.
이전에 출제한 문제 제목을 확인하여 중복을 피합니다.

### 원격 동기화 (GitHub) — 반드시 수행

대상 파일: `data/kata_history.json`, `kata.py`, `SKILL.md` (레포 루트 `~/Desktop/deploy/codekata`).

**세션 시작 시 (첫 문제 출제 전에 1회):**
```bash
cd ~/Desktop/deploy/codekata && git pull --ff-only origin main
```
pull 실패 시: 원인(권한, 충돌, 네트워크)을 사용자에게 한 줄로 알리고, 로컬 파일로 계속 진행합니다.

**세션 종료 시 (마지막 문제의 채점/히스토리 기록 후):**
```bash
cd ~/Desktop/deploy/codekata \
  && git add data/kata_history.json kata.py SKILL.md \
  && (git diff --cached --quiet || git commit -m "kata: session $(date +%F)") \
  && (git push origin main 2>/tmp/kata_push.log \
      || (echo "push 실패 — pull --rebase 후 재시도" && git pull --rebase origin main && git push origin main))
```
- diff가 비어 있으면 커밋/푸시를 건너뜁니다.
- non-fast-forward로 푸시 실패 시 자동으로 `pull --rebase` 후 재푸시.
- 여전히 실패하면 원인을 사용자에게 알리되 로컬 파일은 손상 없이 유지합니다.

`~/.claude/skills/kata/SKILL.md`는 이 파일과 내용이 같아야 합니다. 레포 SKILL.md를 수정하면 다음 명령으로 반영:
```bash
cp ~/Desktop/deploy/codekata/SKILL.md ~/.claude/skills/kata/SKILL.md
```

## 통계 (`/kata stats`)

히스토리를 읽어 아래 형식으로 출력합니다:

```
── 카타 통계 ──

Python  ████████░░░░  8문제 (타이핑 5 / 퀴즈 3)
Rust    ████░░░░░░░░  4문제 (타이핑 2 / 퀴즈 2)
C++     ██░░░░░░░░░░  2문제 (타이핑 1 / 퀴즈 1)

연속 연습: 3일
오늘: 5문제
```

## 연속 출제

숫자를 지정하면 (`/kata python 5`) 해당 수만큼 연속으로 출제합니다.
한 문제를 풀면 바로 다음 문제를 출제합니다.
사용자가 "q"나 "그만"을 입력하면 중단합니다.

## Important

- 정답을 문제와 함께 보여주지 마세요. 사용자가 답을 제출한 뒤에만 공개합니다.
- 타이핑 카타의 힌트는 핵심 키워드/함수명 수준으로 짧게만 제공합니다.
- 매번 새로운 문제를 생성합니다. 같은 문제를 반복하지 않습니다.
- 객관식은 반드시 AskUserQuestion의 options 4개로 보기를 제시합니다.
- 객관식은 1회 기회만 있으므로 선택 즉시 채점합니다.
