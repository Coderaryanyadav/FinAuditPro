"""Native biometric (Apple Touch ID / Device Owner) authentication manager for macOS."""

import os
import subprocess
import sys
from typing import Any


def is_biometrics_available() -> bool:
    """Check if macOS Touch ID or Device Owner authentication is hardware-supported and enrolled."""
    if sys.platform != "darwin":
        return False

    if os.environ.get("FINAUDITPRO_DISABLE_BIOMETRICS") == "1":
        return False

    try:
        import ctypes
        from ctypes import byref, c_bool, c_char_p, c_long, c_void_p

        objc = ctypes.cdll.LoadLibrary("/usr/lib/libobjc.A.dylib")
        ctypes.cdll.LoadLibrary(
            "/System/Library/Frameworks/LocalAuthentication.framework/LocalAuthentication"
        )

        objc.objc_getClass.restype = c_void_p
        objc.objc_getClass.argtypes = [c_char_p]
        objc.sel_registerName.restype = c_void_p
        objc.sel_registerName.argtypes = [c_char_p]

        LAContextClass = objc.objc_getClass(b"LAContext")
        if not LAContextClass:
            return False

        alloc_sel = objc.sel_registerName(b"alloc")
        init_sel = objc.sel_registerName(b"init")
        can_eval_sel = objc.sel_registerName(b"canEvaluatePolicy:error:")

        msg_send = ctypes.CFUNCTYPE(c_void_p, c_void_p, c_void_p)(("objc_msgSend", objc))
        context = msg_send(LAContextClass, alloc_sel)
        context = msg_send(context, init_sel)

        can_eval = ctypes.CFUNCTYPE(c_bool, c_void_p, c_void_p, c_long, c_void_p)(
            ("objc_msgSend", objc)
        )
        err: Any = c_void_p(0)
        # LAPolicyDeviceOwnerAuthentication = 2 (Touch ID or passcode)
        return bool(can_eval(context, can_eval_sel, 2, byref(err)))
    except Exception:
        return False


def authenticate_with_biometrics(
    reason: str = "Unlock FinAuditPro Workstation", timeout_seconds: int = 30
) -> bool:
    """Evaluate Touch ID / Device Owner authentication via native macOS security prompt."""
    if not is_biometrics_available():
        return False

    swift_script = f"""
import LocalAuthentication
import Foundation

let context = LAContext()
var error: NSError?
let sema = DispatchSemaphore(value: 0)
var authSuccess = false

if context.canEvaluatePolicy(.deviceOwnerAuthentication, error: &error) {{
    context.evaluatePolicy(.deviceOwnerAuthentication, localizedReason: "{reason}") {{ success, _ in
        authSuccess = success
        sema.signal()
    }}
    _ = sema.wait(timeout: .now() + {timeout_seconds})
}}
exit(authSuccess ? 0 : 1)
"""
    try:
        proc = subprocess.run(  # noqa: S603
            ["/usr/bin/swift", "-e", swift_script],
            capture_output=True,
            timeout=timeout_seconds + 2,
        )
        return proc.returncode == 0
    except Exception:
        return False
