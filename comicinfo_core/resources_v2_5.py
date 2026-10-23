"""Hardware capacity discovery and resource-setting validation."""

from __future__ import annotations

import ctypes
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class HardwareCapacity:
    logical_cpus: int
    physical_cpus: int
    physical_memory_bytes: int | None


COMPRESSION_MEMORY_RESERVE_BYTES = 64 * 1024 * 1024


def get_hardware_capacity() -> HardwareCapacity:
    logical_cpus = max(1, os.cpu_count() or 1)
    physical_cpus = _physical_cpu_count(logical_cpus)
    memory_bytes = _physical_memory_bytes()
    return HardwareCapacity(
        logical_cpus=logical_cpus,
        physical_cpus=max(1, min(physical_cpus, logical_cpus)),
        physical_memory_bytes=memory_bytes,
    )


def get_process_memory_usage_bytes() -> int | None:
    """Return current process resident memory, if the platform exposes it."""
    if sys.platform == "win32":
        try:
            class ProcessMemoryCounters(ctypes.Structure):
                _fields_ = [
                    ("cb", ctypes.c_ulong),
                    ("PageFaultCount", ctypes.c_ulong),
                    ("PeakWorkingSetSize", ctypes.c_size_t),
                    ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t),
                    ("PeakPagefileUsage", ctypes.c_size_t),
                ]

            counters = ProcessMemoryCounters()
            counters.cb = ctypes.sizeof(counters)
            current_process = ctypes.windll.kernel32.GetCurrentProcess()
            succeeded = ctypes.windll.psapi.GetProcessMemoryInfo(
                current_process,
                ctypes.byref(counters),
                counters.cb,
            )
            return int(counters.WorkingSetSize) if succeeded else None
        except (AttributeError, OSError):
            return None

    if sys.platform == "darwin":
        value = _run_command(["ps", "-o", "rss=", "-p", str(os.getpid())])
        if value and value.isdigit():
            return int(value) * 1024

    if sys.platform.startswith("linux"):
        try:
            for line in Path("/proc/self/status").read_text(encoding="ascii").splitlines():
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) * 1024
        except (OSError, ValueError, IndexError):
            return None

    return None


def get_available_memory_bytes() -> int | None:
    """Return a best-effort estimate of currently available physical memory."""
    if sys.platform == "win32":
        try:
            class MemoryStatus(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            status = MemoryStatus()
            status.dwLength = ctypes.sizeof(status)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                return int(status.ullAvailPhys)
        except (AttributeError, OSError):
            return None

    if sys.platform == "darwin":
        output = _run_command(["vm_stat"])
        if output:
            page_match = re.search(r"page size of (\d+) bytes", output)
            if page_match:
                page_size = int(page_match.group(1))
                page_counts = {}
                for name in ("free", "inactive", "speculative"):
                    match = re.search(rf"Pages {name}:\s+(\d+)", output)
                    if match:
                        page_counts[name] = int(match.group(1))
                if page_counts:
                    return sum(page_counts.values()) * page_size

    if sys.platform.startswith("linux"):
        try:
            for line in Path("/proc/meminfo").read_text(encoding="ascii").splitlines():
                if line.startswith("MemAvailable:"):
                    return int(line.split()[1]) * 1024
        except (OSError, ValueError, IndexError):
            return None

    return None


def limit_compression_workers(workers: int, memory_limit_percent: int) -> int:
    """Fit compression concurrency to a soft resident-memory budget.

    The estimate reserves 64 MiB per active compressor. This is a scheduling
    safeguard, not an operating-system memory cap.
    """
    capacity = get_hardware_capacity()
    process_memory = get_process_memory_usage_bytes()
    total_memory = capacity.physical_memory_bytes
    if process_memory is None or total_memory is None:
        return workers

    memory_budget = total_memory * memory_limit_percent // 100
    remaining_budget = memory_budget - process_memory
    available_memory = get_available_memory_bytes()
    if available_memory is not None:
        remaining_budget = min(remaining_budget, available_memory)
    available_workers = remaining_budget // COMPRESSION_MEMORY_RESERVE_BYTES
    return min(workers, max(0, available_workers))


def _run_command(arguments: list[str]) -> str | None:
    try:
        result = subprocess.run(
            arguments,
            check=True,
            capture_output=True,
            text=True,
            timeout=3,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip()


def _physical_cpu_count(logical_cpus: int) -> int:
    if sys.platform == "darwin":
        value = _run_command(["sysctl", "-n", "hw.physicalcpu"])
        if value and value.isdigit():
            return int(value)

    if sys.platform.startswith("linux"):
        topology_paths = sorted(
            Path("/sys/devices/system/cpu").glob("cpu[0-9]*/topology/core_id")
        )
        core_pairs = set()
        for core_path in topology_paths:
            try:
                core_id = core_path.read_text(encoding="ascii").strip()
                package_path = core_path.with_name("physical_package_id")
                package_id = package_path.read_text(encoding="ascii").strip()
                core_pairs.add((package_id, core_id))
            except OSError:
                continue
        if core_pairs:
            return len(core_pairs)

        cpuinfo_path = "/proc/cpuinfo"
        try:
            cpuinfo = Path(cpuinfo_path).read_text(encoding="ascii")
            sections = re.split(r"\n\s*\n", cpuinfo)
            core_pairs = set()
            for section in sections:
                values = dict(
                    line.split(":", 1)
                    for line in section.splitlines()
                    if ":" in line
                )
                if "core id" in values:
                    core_pairs.add(
                        (values.get("physical id", "0"), values["core id"].strip())
                    )
            if core_pairs:
                return len(core_pairs)
        except OSError:
            pass

    if sys.platform == "win32":
        command = (
            "(Get-CimInstance Win32_Processor | "
            "Measure-Object -Property NumberOfCores -Sum).Sum"
        )
        value = _run_command(["powershell", "-NoProfile", "-Command", command])
        if value and value.isdigit():
            return int(value)

    return logical_cpus


def _physical_memory_bytes() -> int | None:
    if sys.platform == "darwin":
        value = _run_command(["sysctl", "-n", "hw.memsize"])
        if value and value.isdigit():
            return int(value)

    if sys.platform == "win32":
        try:
            class MemoryStatus(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            status = MemoryStatus()
            status.dwLength = ctypes.sizeof(status)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                return int(status.ullTotalPhys)
        except (AttributeError, OSError):
            return None

    if hasattr(os, "sysconf"):
        try:
            page_size = os.sysconf("SC_PAGE_SIZE")
            page_count = os.sysconf("SC_PHYS_PAGES")
            if page_size > 0 and page_count > 0:
                return int(page_size * page_count)
        except (OSError, ValueError):
            return None

    return None
