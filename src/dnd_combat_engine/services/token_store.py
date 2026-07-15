"""Secure per-user storage for the GitHub bug-report token."""

from __future__ import annotations

import ctypes
import os
from ctypes import wintypes
from pathlib import Path

_DPAPI_HEADER = b"DNDCE-DPAPI-1\0"


class _DataBlob(ctypes.Structure):
    _fields_ = (("size", wintypes.DWORD), ("data", ctypes.POINTER(ctypes.c_char)))


class UserTokenStore:
    """Store a token encrypted for the current Windows user with DPAPI."""

    def __init__(self, path: Path | str) -> None:
        """Initialize storage at a per-user settings path."""
        self.path = Path(path)

    def save(self, token: str) -> None:
        """Encrypt and persist a non-empty token for the current OS user."""
        value = token.strip()
        if not value:
            raise ValueError("GitHub token cannot be empty.")
        if os.name != "nt":
            raise OSError("Secure token storage is available only on Windows.")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_bytes(_DPAPI_HEADER + _protect_data(value.encode("utf-8")))

    def load(self) -> str | None:
        """Return the decrypted token, or None when no token has been saved."""
        if not self.path.exists():
            return None
        payload = self.path.read_bytes()
        if not payload.startswith(_DPAPI_HEADER):
            raise OSError("The saved GitHub token has an unsupported format.")
        if os.name != "nt":
            raise OSError("The saved GitHub token can only be decrypted on Windows.")
        return _unprotect_data(payload[len(_DPAPI_HEADER) :]).decode("utf-8").strip() or None

    def clear(self) -> None:
        """Remove the saved token if one exists."""
        self.path.unlink(missing_ok=True)


def _blob(data: bytes) -> tuple[_DataBlob, ctypes.Array[ctypes.c_char]]:
    buffer = ctypes.create_string_buffer(data)
    return _DataBlob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_char))), buffer


def _protect_data(data: bytes) -> bytes:
    input_blob, input_buffer = _blob(data)
    output_blob = _DataBlob()
    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32
    if not crypt32.CryptProtectData(
        ctypes.byref(input_blob),
        "DnDCombatEngine GitHub bug reports",
        None,
        None,
        None,
        0,
        ctypes.byref(output_blob),
    ):
        raise ctypes.WinError()
    del input_buffer
    try:
        return ctypes.string_at(output_blob.data, output_blob.size)
    finally:
        kernel32.LocalFree(output_blob.data)


def _unprotect_data(data: bytes) -> bytes:
    input_blob, input_buffer = _blob(data)
    output_blob = _DataBlob()
    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32
    if not crypt32.CryptUnprotectData(
        ctypes.byref(input_blob),
        None,
        None,
        None,
        None,
        0,
        ctypes.byref(output_blob),
    ):
        raise ctypes.WinError()
    del input_buffer
    try:
        return ctypes.string_at(output_blob.data, output_blob.size)
    finally:
        kernel32.LocalFree(output_blob.data)
