# Math Rules

## 핵심 원칙

- 수식은 **LaTeX 형태로 유지**한다
- 수식 자체의 의미·구조 변경 금지
- 의미 설명은 별도로 (수식 카드의 `what` / `why` / `links` 필드 또는 본문 산문)

---

## 표기 규약

### 인라인 수식
```
$X_t$, $\alpha = 0.5$
```

### Display 수식
```
$$
S_t = \frac{X_{t-P}^\top X_t}{\|X_{t-P}\|\,\|X_t\|}
$$
```

### JSON 안의 LaTeX
JSON 문자열 안에서는 백슬래시를 이중으로 이스케이프한다:

```json
{ "tex": "S_t = \\frac{X_{t-P}^\\top X_t}{\\|X_{t-P}\\|\\,\\|X_t\\|}" }
```

### 🔴 부등호·꺾쇠 — HTML 태그 수프 금지 (정책, 2026-07-08)

HTML에 raw 삽입되는 문자열(번역문, tabs_data의 body/where/intuition, tex 블록)에서
**`<` 뒤에 영문자가 오는 표기를 그대로 쓰면 브라우저가 태그로 파싱**해, 그 지점 이후
문서 전체가 `<b>`/`<i>`로 재구성되는 태그 수프가 생긴다.

- tex 안: `<` → `\\lt`, `>` → `\\gt` (예: `X_{a\\lt i}`, `\\ell \\lt k`)
- 일반 텍스트(번역·body·where 등): `&lt;` / `&gt;` (예: `y_&lt;t`, `0.1&lt;IOU&lt;0.5`)
- `< 0.45`처럼 `<` 뒤가 공백·숫자면 파서상 안전하지만, 통일성을 위해 `&lt;` 권장.
- 검증 의무: 데이터 작성/수정 후 `python tools/check_html_escape.py "papers/N. name"` 실행 — 0건이어야 빌드 진행.

> 정본 학습 사례 (실패→복구): `24. geollava8k` Eq 5의 `X_{a<i}`가 태그로 파싱되어 수식 탭
> 이후 문서 전체가 굵게 렌더 (2026-07-08 발견). 전수 스캔에서 10. yolo(`0.1<IOU<0.5`),
> 25. visiondrop(`y_<t`)도 같은 유형 발견·수정. 이 정책과 검사 도구의 직접 동기.

---

## MathJax 통합

- 빌더는 MathJax 3을 CDN으로 로드 (`tex-svg.js` 또는 `tex-chtml.js`)
- 설정:
  ```js
  MathJax = {
    tex: {
      inlineMath: [['$', '$'], ['\\(', '\\)']],
      displayMath: [['$$', '$$'], ['\\[', '\\]']],
      processEscapes: true
    },
    svg: { fontCache: 'global' },
    options: { skipHtmlTags: ['script','noscript','style','textarea','pre','code'] }
  };
  ```
- **탭 전환 시 재렌더 필수:** 탭 전환 JS에서 `MathJax.typesetPromise()` 호출

---

## 수식 패치 (폐기 - 구 `apply_math_latex.py` 절차)

> **폐기 (2026-09-10 확인)**: 평문 수식을 사후에 LaTeX 로 패치하는 스크립트 `apply_math_latex.py` 는 저장소에 존재한 적이 없다. 변환 자체는 Stage 2 에서 `structured.json` 을 작성할 때 직접 수행한다 (`prompts/02_structuring.md` 규칙 3). 아래 규칙은 그 작성 규칙으로만 유효하다.

- 본문(`structured.json`)과 번역(`translations/manual.json`) 양쪽에 동일한 `$...$` / `$$...$$` 블록을 바이트 단위로 복사한다 (정본 생성기: `papers/27. lupi/_mk_structured.py`)
- 인라인 수식(예: `S_t`, `X_{t-P}`)은 `$...$`로 감싼다
- Display 수식 블록(예: 식 1, 2, 3)은 `$$...$$`로 감싼다
- 이미 `$` 안에 들어 있는 부분을 다시 감싸지 않는다

---

## 식별자 / 참조

### Equation ID
- `eq1_<keyword>`, `eq2_<keyword>`, ... 일관된 명명
- `tabs_data/knowledge.json#equations`의 `eq_id`와 일치

### Ref-link 자동 anchor
본문에 등장하는 수식 참조는 자동으로 다른 탭으로 점프 가능한 링크로 감싸진다:

| 패턴 | 점프 대상 |
|---|---|
| `Eq. N` / `Equation N` | ③ `tab-knowledge` 의 해당 `eq_id` |
| `Fig. N` / `Figure N` | ① `tab-reading` 의 해당 자산 |
| `Table N` | ① `tab-reading` 의 해당 자산 |

단일 HTML의 인라인 JS(`autoLink()`)가 텍스트 노드를 스캔해 `<a class="ref-link" data-target-tab="...">`로 자동 wrap.

---

## 절대 금지

- 수식의 변수명 / 심볼 임의 변경
- 수식 내부 LaTeX 명령어를 한글로 번역
- 수식을 평문(`X_t`를 `Xt`로 등)으로 평탄화
- LaTeX 이스케이프 누락 (JSON에서 `\\` 두 번 필수)
- MathJax 재렌더 누락 (탭 전환 후 수식이 raw `$...$`로 남는 버그 주의)
