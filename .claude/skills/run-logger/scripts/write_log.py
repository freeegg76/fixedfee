"""
실행 로그 append 및 summary JSON 생성/업데이트.

사용법:
  # 로그 한 줄 추가
  python write_log.py --log-path output/run_202503.log \
    --level SUCCESS --client "고객사A" --message "탭: 2025.03 | URL: https://..."

  # START/END 로그 (client 없음)
  python write_log.py --log-path output/run_202503.log \
    --level START --message "귀속월: 2025/03"

  # summary JSON 작성
  python write_log.py --summary-path output/summary_202503.json \
    --summary-json '{"run_month":"2025/03", ...}'
"""

import argparse
import json
import os
import sys
from datetime import datetime


def append_log(log_path: str, level: str, message: str, client: str | None = None):
    os.makedirs(os.path.dirname(log_path) if os.path.dirname(log_path) else ".", exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if client:
        line = f"[{timestamp}] {level} | {client} | {message}\n"
    else:
        line = f"[{timestamp}] {level} | {message}\n"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(line)
    print(json.dumps({"logged": line.strip()}))


def write_summary(summary_path: str, summary_dict: dict):
    os.makedirs(os.path.dirname(summary_path) if os.path.dirname(summary_path) else ".", exist_ok=True)
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary_dict, f, ensure_ascii=False, indent=2)
    print(json.dumps({"summary_written": summary_path}))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--log-path", default=None)
    parser.add_argument("--level", default=None,
                        choices=["START", "SUCCESS", "SKIP", "ERROR", "END", "INFO"])
    parser.add_argument("--client", default=None)
    parser.add_argument("--message", default=None)
    parser.add_argument("--summary-path", default=None)
    parser.add_argument("--summary-json", default=None)
    args = parser.parse_args()

    if args.summary_path and args.summary_json:
        try:
            summary_dict = json.loads(args.summary_json)
        except json.JSONDecodeError as e:
            print(json.dumps({"error": f"summary-json 파싱 실패: {e}"}))
            sys.exit(1)
        write_summary(args.summary_path, summary_dict)
        return

    if args.log_path and args.level and args.message:
        append_log(args.log_path, args.level, args.message, args.client)
        return

    print(json.dumps({"error": "인수 조합이 올바르지 않습니다. --help 참조"}))
    sys.exit(1)


if __name__ == "__main__":
    main()
