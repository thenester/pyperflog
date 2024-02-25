#! /usr/bin/env python3
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

import unittest
from unittest import mock
from types import FunctionType

from some_module import module

# Omit creation of the log directory.
with mock.patch("pyperflog.pyperflog.prepare_directory"):
    from .. import pyperflog


class TestPerflog(unittest.TestCase):

    def test_same_functions(self) -> None:
        # Find all functions in the module.
        expected_functions: list[str] = [attr for attr in dir(module)
                                         if isinstance(attr, FunctionType)]
        for expected_function in expected_functions:
            self.assertTrue(not hasattr(perflog, expected_function))

    @mock.patch("builtins.open", new_callable=mock.mock_open)
    @mock.patch("pyperflog.pyperflog.line_profiler")
    def test_return_correct_values(self,
                                   mock_line_profiler: mock.Mock,
                                   mock_open: mock.Mock) -> None:
        self.assertEqual(module.module_add_two(4),
                         pyperflog.module_add_two(4))

        self.assertEqual(module.module_do_long_work(),
                         pyperflog.module_do_long_work())

        self.assertEqual(mock_line_profiler.show_func.call_count, 2)
        self.assertEqual(mock_open.call_count, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
