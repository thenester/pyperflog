# MIT License
#
# Copyright (c) 2024 Denys Nesterenko
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
This module is intended to be a copy of `PROFILER_DECORATE_MODULE` from a functional standpoint.
It extends all functions of the `PROFILER_DECORATE_MODULE` by decorating them with `performance`.
The `performance` decorator utilizes `LineProfiler` to gather performance metrics, and store them
in the following directory `PROFILER_LOG_ROOT_PATH`/<process_name>/<function_name>.
The metrics are updated as functions gets called through this module.

Usage:
    1. Place this module in the directory where `PROFILER_DECORATE_MODULE` is located.
    2. Rename the `PROFILER_DECORATE_MODULE` to some `PROFILER_DECORATE_MODULE_NEW` (any name).
    3. Rename this module to `PROFILER_DECORATE_MODULE` original name.
    4. Update import of the `PROFILER_DECORATE_MODULE` in this module
       to `PROFILER_DECORATE_MODULE_NEW`.
    5. Update value stored in `PROFILER_DECORATE_MODULE` to `PROFILER_DECORATE_MODULE_NEW`.
    6. Reload any user-process with the name <process_name>
       to use this module instead of `PROFILER_DECORATE_MODULE`.
    7. Wait until user-process calls any function using this module.
    8. Collect performance metrics in the `PROFILER_LOG_ROOT_PATH`/<process_name>.
"""

import inspect
import os
import subprocess
import sys
from contextlib import contextmanager
from threading import Event, Lock
from types import ModuleType
from typing import IO, Any, Callable, Generator, Optional

import line_profiler
from line_profiler import LineProfiler

from some_module import module

# The module functions of which should be decorated.
PROFILER_DECORATE_MODULE = module
PROFILER_DECORATE_FUNCTIONS_WITH_PREFIX = "module_"
PROFILER_LOG_ROOT_PATH = "performance_log"
PROFILER = None

__already_overwritten = Event()
__overwrite_lock = Lock()


def get_process_name() -> str:
    """Returns the name of the process.

    Returns:
        str: process name
    """
    pid = os.getpid()
    process_name = None
    with subprocess.Popen(f"ps -q {pid} -o comm=", shell=True, stdout=subprocess.PIPE) as proc:
        out, err = proc.communicate()
        if not err:
            process_name = out.decode().strip()

    return process_name if process_name else f"{pid}"


def prepare_directory(path: str) -> bool:
    """Creates the directory if it is not created.

    Args:
        path (str): path to the directory should be created.

    Returns:
        bool: True if succeeded, False otherwise.
    """
    try:
        os.makedirs(path, exist_ok=True)
    except OSError:
        return False

    return True


@contextmanager
def write_stdout_to_file(file_path: str, write_mode: str = "a") -> Generator[IO[Any], None, None]:
    """Replaces stdout with TextIOWrapper of the opened `file_path`.

    Args:
        file_path (str): path to the file should be opened.
        write_mode (str): mode to open the file. Defaults to "a".

    Yields:
        Generator[IO[Any], None, None]: replaced stdout.
    """
    prev_stdout = sys.stdout
    sys.stdout = open(file_path, write_mode, encoding="utf-8")
    yield sys.stdout
    sys.stdout.close()
    sys.stdout = prev_stdout


def update_func_stats(profiler: LineProfiler,
                      func: Callable,
                      profiler_log_path: str) -> None:
    """Updates performance metrics of `func` and writes them into the log file.

    Args:
        profiler (LineProfiler): object of LineProfiler.
        func (Callable): function which performance needs to be updated.
        profiler_log_path (str): path to the profiler logs for current process.
    """
    func_name = func.__name__
    func_file_name = func.__code__.co_filename
    func_start_line = func.__code__.co_firstlineno

    # Receive all current timings.
    stats = profiler.get_stats()
    # Find timing for a specific function.
    timing = stats.timings.get((func_file_name, func_start_line, func_name))
    if not timing:
        return

    with open(f"{profiler_log_path}/{func_name}", "a", encoding="utf-8") as profile_log:
        line_profiler.show_func(func_file_name,
                                func_start_line,
                                func_name,
                                timing,
                                stats.unit,
                                stream=profile_log)


def performance(profiler: LineProfiler,
                func: Callable,
                profiler_log_path: str) -> Callable:
    """Decorator to wrap-up function and update performance metrics on each call.

    Args:
        profiler (LineProfiler): object of LineProfiler.
        func (Callable): any function.
        profiler_log_path (str): path to the profiler logs for current process.
    """
    def wrapper(*args, **kwargs):
        lp_wrapper = profiler(func)
        result = lp_wrapper(*args, **kwargs)
        update_func_stats(profiler, func, profiler_log_path)
        return result
    return wrapper


def decorate_module_functions(target_module: ModuleType,
                              profiler: LineProfiler,
                              profiler_log_path: str,
                              func_name_prefix: Optional[str] = None) -> None:
    """Finds all functions in `module` (optionally by function prefix name),
       and decorates them with `performance`. Decorated functions are exposed
       as globals of the current module.

    Args:
        target_module (ModuleType): module which in all functions will be decorated.
        profiler (LineProfiler): object of LineProfiler.
        profiler_log_path (str): path to the profiler logs for current process.
        func_name_prefix (Optional[str], optional): _description_. Defaults to None.
    """
    for attr, pointer in target_module.__dict__.items():
        if not inspect.isfunction(pointer):
            continue
        if func_name_prefix and not attr.startswith(func_name_prefix):
            continue
        inspect.stack()[0][0].f_globals[attr] = performance(
            profiler, pointer, profiler_log_path)


# The main routine to decorate all functions in the `PROFILER_DECORATE_MODULE`.
if not __already_overwritten.is_set():
    with __overwrite_lock:
        profiler_process_log = f"{PROFILER_LOG_ROOT_PATH}/{get_process_name()}"
        prepare_directory(profiler_process_log)
        PROFILER = LineProfiler()
        decorate_module_functions(PROFILER_DECORATE_MODULE,
                                  PROFILER,
                                  profiler_process_log,
                                  PROFILER_DECORATE_FUNCTIONS_WITH_PREFIX)
        __already_overwritten.set()
