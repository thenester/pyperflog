# Pyperflog

This repository intention is to provide a single python module `pyperflog.py` that helps to facalitate gathering of python code performance using `line_profiler`.

The `pyperflog.py` operates as a wrapper for the module defined by `PROFILER_DECORATE_MODULE` whose performance is under the testing.

It is doing so by extends all functions of the `PROFILER_DECORATE_MODULE` by decorating them with `performance`.

The `performance` decorator utilizes `LineProfiler` to gather performance metrics, and store them
in the following directory `PROFILER_LOG_ROOT_PATH`/<process_name>/<function_name>.

The metrics are updated as functions gets called through this module.

## Dependencies

- [line_profiler](https://github.com/pyutils/line_profiler)

## Usage

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