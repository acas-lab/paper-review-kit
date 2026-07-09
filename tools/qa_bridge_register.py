# -*- coding: utf-8 -*-
r"""qa_bridge_register.py — `qabridge://` 커스텀 URL 프로토콜을 Windows(HKCU)에 등록.

이 프로토콜을 한 번 등록해 두면, 학습 HTML의 'Q&A 생성' / '검토 결과 파악하기' 버튼이
브릿지가 꺼져 있을 때 `qabridge://start` 를 열고, Windows 가 tools/qa_bridge_start.bat 을
실행해 브릿지를 자동으로 켠다. 이후 버튼 클릭만으로 브릿지가 뜬다(관리자 권한 불필요 — HKCU).

  등록:   python tools/qa_bridge_register.py
  해제:   python tools/qa_bridge_register.py --unregister
  확인:   python tools/qa_bridge_register.py --status

동작: HKEY_CURRENT_USER\Software\Classes\qabridge 에
  (기본값)          = "URL:QA Bridge Protocol"
  "URL Protocol"    = ""
  shell\open\command\(기본값) = "\"<repo>\tools\qa_bridge_start.bat\" \"%1\""

정본: 2026-07-09.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BAT = ROOT / "tools" / "qa_bridge_start.bat"
PROTO = "qabridge"
KEYPATH = r"Software\Classes\%s" % PROTO


def register():
    import winreg
    cmd = '"%s" "%%1"' % str(BAT)
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, KEYPATH) as k:
        winreg.SetValueEx(k, None, 0, winreg.REG_SZ, "URL:QA Bridge Protocol")
        winreg.SetValueEx(k, "URL Protocol", 0, winreg.REG_SZ, "")
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, KEYPATH + r"\shell\open\command") as k:
        winreg.SetValueEx(k, None, 0, winreg.REG_SZ, cmd)
    print("[OK] qabridge:// 등록 완료")
    print("     command =", cmd)
    print("     이제 학습 HTML의 버튼을 누르면 브릿지가 자동으로 켜집니다.")
    print("     (브라우저가 최초 1회 '열기' 확인을 물으면 허용 + '항상 허용' 체크 권장)")


def unregister():
    import winreg

    def rm(path):
        # 하위 키부터 삭제
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path) as k:
                while True:
                    try:
                        sub = winreg.EnumKey(k, 0)
                    except OSError:
                        break
                    rm(path + "\\" + sub)
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, path)
        except FileNotFoundError:
            pass

    rm(KEYPATH)
    print("[OK] qabridge:// 등록 해제 완료")


def status():
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, KEYPATH + r"\shell\open\command") as k:
            val, _ = winreg.QueryValueEx(k, None)
        print("[등록됨] command =", val)
        if not BAT.exists():
            print("  ⚠ 경고: 런처 배치가 없습니다:", BAT)
    except FileNotFoundError:
        print("[미등록] python tools/qa_bridge_register.py 로 등록하세요.")


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    if sys.platform != "win32":
        raise SystemExit("이 도구는 Windows 전용입니다 (winreg).")
    if not BAT.exists():
        print("⚠ 런처 배치가 없습니다:", BAT, "— tools/qa_bridge_start.bat 을 먼저 확인하세요.")
    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    if arg in ("--unregister", "-u"):
        unregister()
    elif arg in ("--status", "-s"):
        status()
    else:
        register()


if __name__ == "__main__":
    main()
