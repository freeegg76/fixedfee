# Skill: run-logger

실행 로그 파일에 결과를 append하고, 최종 summary JSON을 생성/갱신하는 스킬.

## 스크립트

`.claude/skills/run-logger/scripts/write_log.py`

---

## 모드 1: 로그 한 줄 추가

### 호출 방법

```bash
# START / END (고객사 없음)
python .claude/skills/run-logger/scripts/write_log.py \
  --log-path "output/run_202503.log" \
  --level START \
  --message "귀속월: 2025/03"

# 고객사별 결과 (SUCCESS / SKIP / ERROR)
python .claude/skills/run-logger/scripts/write_log.py \
  --log-path "output/run_202503.log" \
  --level SUCCESS \
  --client "삼성전자" \
  --message "탭: 2025.03 | URL: https://docs.google.com/spreadsheets/d/..."
```

### 로그 파일 형식

```
[2025-03-01 09:00:01] START | 귀속월: 2025/03
[2025-03-01 09:00:03] SUCCESS | 삼성전자 | 탭: 2025.03 | URL: https://...
[2025-03-01 09:00:07] SKIP | LG전자 | 탭 이미 존재: 2025.03
[2025-03-01 09:00:09] ERROR | SK하이닉스 | Key 없음 (Fixed 탭, CoCd: C003)
[2025-03-01 09:00:15] END | 총 3건 | 성공 1 / 스킵 1 / 실패 1
```

### 레벨 종류

| 레벨 | 사용 시점 |
|------|----------|
| `START` | 배치 시작 시 |
| `SUCCESS` | 고객사 처리 성공 |
| `SKIP` | 탭 이미 존재 / Key 없음 으로 스킵 |
| `ERROR` | 재시도 후에도 실패 |
| `END` | 배치 완료 시 |
| `INFO` | 기타 정보성 메시지 |

---

## 모드 2: Summary JSON 작성

### 호출 방법

```bash
python .claude/skills/run-logger/scripts/write_log.py \
  --summary-path "output/summary_202503.json" \
  --summary-json '{
    "run_month": "2025/03",
    "executed_at": "2025-03-01T09:00:15",
    "total": 3,
    "success": 1,
    "skipped": 1,
    "failed": 1,
    "results": [...]
  }'
```

### 로그/요약 파일 경로 규칙

- `YYYYMM`은 귀속월에서 `/`를 제거한 값 (예: `2025/03` → `202503`)
- 로그: `output/run_202503.log`
- 요약: `output/summary_202503.json`
