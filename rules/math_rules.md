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

## 수식 패치 (`apply_math_latex.py`)

PDF에서 추출된 평문 수식을 LaTeX/MathJax 인식 형태로 변환하는 idempotent 스크립트.

- 본문(`structured.json`)과 번역(`translated.json`) 양쪽에 동일 패치 적용
- 인라인 수식 후보(예: `S_t`, `X_{t-P}`)를 `$...$`로 감쌈
- Display 수식 블록(예: 식 1, 2, 3)을 `$$...$$`로 감쌈
- 한 번 패치된 부분은 다시 처리하지 않음 (이미 `$` 안에 들어 있으면 skip)

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
