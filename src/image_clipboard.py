# DalleCraft
#
# Copyright (c) 2025-2026 led-mirage
# このソースコードは MITライセンス の下でライセンスされています。
# ライセンスの詳細については、このプロジェクトのLICENSEファイルを参照してください。

import ctypes
import io
import sys
import time
from ctypes import wintypes

from PIL import Image, ImageOps


CF_DIB = 8
GMEM_MOVEABLE = 0x0002


def image_to_dib(image_path: str) -> bytes:
    """画像をWindowsクリップボードのCF_DIB形式へ変換する。"""
    with Image.open(image_path) as image:
        image = ImageOps.exif_transpose(image).convert("RGB")
        output = io.BytesIO()
        image.save(output, format="BMP")

    # CF_DIBにはBMPファイルヘッダー（先頭14バイト）を含めない。
    return output.getvalue()[14:]


def copy_image_to_clipboard(image_path: str) -> None:
    """画像をWindowsクリップボードへ画像データとしてコピーする。"""
    if sys.platform != "win32":
        raise RuntimeError("画像のクリップボードコピーはWindowsでのみ利用できます。")

    dib = image_to_dib(image_path)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    user32 = ctypes.WinDLL("user32", use_last_error=True)

    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
    kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalUnlock.restype = wintypes.BOOL
    kernel32.GlobalFree.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalFree.restype = wintypes.HGLOBAL
    kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
    kernel32.GetModuleHandleW.restype = wintypes.HMODULE

    user32.OpenClipboard.argtypes = [wintypes.HWND]
    user32.OpenClipboard.restype = wintypes.BOOL
    user32.EmptyClipboard.argtypes = []
    user32.EmptyClipboard.restype = wintypes.BOOL
    user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
    user32.SetClipboardData.restype = wintypes.HANDLE
    user32.CloseClipboard.argtypes = []
    user32.CloseClipboard.restype = wintypes.BOOL
    user32.CreateWindowExW.argtypes = [
        wintypes.DWORD,
        wintypes.LPCWSTR,
        wintypes.LPCWSTR,
        wintypes.DWORD,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        wintypes.HWND,
        wintypes.HMENU,
        wintypes.HINSTANCE,
        wintypes.LPVOID,
    ]
    user32.CreateWindowExW.restype = wintypes.HWND
    user32.DestroyWindow.argtypes = [wintypes.HWND]
    user32.DestroyWindow.restype = wintypes.BOOL

    memory = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(dib))
    if not memory:
        raise ctypes.WinError(ctypes.get_last_error())

    # OpenClipboardには所有者となるウィンドウを渡す必要があるため、
    # クリップボード操作の間だけ非表示ウィンドウを作成する。
    owner_window = user32.CreateWindowExW(
        0,
        "STATIC",
        "DalleCraft Clipboard",
        0,
        0,
        0,
        0,
        0,
        None,
        None,
        kernel32.GetModuleHandleW(None),
        None,
    )
    if not owner_window:
        kernel32.GlobalFree(memory)
        raise ctypes.WinError(ctypes.get_last_error())

    clipboard_open = False
    clipboard_owns_memory = False
    try:
        pointer = kernel32.GlobalLock(memory)
        if not pointer:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            ctypes.memmove(pointer, dib, len(dib))
        finally:
            kernel32.GlobalUnlock(memory)

        # 他のアプリが一時的に使用中の場合に備えて短時間だけ再試行する。
        for _ in range(10):
            if user32.OpenClipboard(owner_window):
                clipboard_open = True
                break
            time.sleep(0.05)
        if not clipboard_open:
            raise RuntimeError("クリップボードを開けませんでした。")

        if not user32.EmptyClipboard():
            raise ctypes.WinError(ctypes.get_last_error())
        if not user32.SetClipboardData(CF_DIB, memory):
            raise ctypes.WinError(ctypes.get_last_error())
        clipboard_owns_memory = True
    finally:
        if clipboard_open:
            user32.CloseClipboard()
        if not clipboard_owns_memory:
            kernel32.GlobalFree(memory)
        user32.DestroyWindow(owner_window)
