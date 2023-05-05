#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \ison\run.py
# Created Date: Tuesday, February 15th 2022, 10:16:25 am
# Author: Christian Perwass (CR/AEC5)
# <LICENSE id="Apache-2.0">
#
#   Functional JSON module
#   Copyright 2022 Robert Bosch GmbH and its subsidiaries
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# </LICENSE>
###

import ison


class TestClass:

    ################################################################################
    def test_recurse_01(self):
        dicData = {
            "__func_globals__": {
                "polite": "$L{my dear %0}",
                "greeting": "$L{Hello %0}",
                "greet": "${greeting, ${polite}}",
            },
            "say": "${greet, Christian}",
        }

        xResult: dict = ison.run.Run(xData=dicData, bStripVars=False)

        assert xResult["say"] == "Hello my dear Christian"

    # enddef

    ################################################################################
    def test_strip_01(self):
        dicData = {
            "__func_globals__": {
                "func": "$L{`Hello to %3, %6`}",
            },
            "__globals__": {
                "x": "let's go",
                "greet": "$L{`Hello %0, ${x}`}",
            },
            "say": "${greet, Christian}",
            "say2": "${func, you, Christian}",
        }

        xResult: dict = ison.run.Run(xData=dicData, bStripVars=False)

        assert xResult["say"] == "Hello Christian, let's go"
        assert xResult["say2"] == "Hello to you, Christian"

    # enddef

    ################################################################################
    def test_norm_args_01(self):
        dicData = {
            "__func_globals__": {
                "func": "$L{`Hello to %3, %6`}",
                "func2": "$L{'Hello to %3, %6'}",
            },
            "__globals__": {
                "x": "lets go",
                "greet": "$L{`Hello %0, ${x}`}",
            },
            "say": "${func, you, Christian}",
            "say2": "${func2, you, Christian}",
        }

        xResult: dict = ison.run.Run(xData=dicData, bStripVars=False)

        assert xResult["say"] == "Hello to you, Christian"
        assert xResult["say2"] == "'Hello to you, Christian'"

    # enddef

    ################################################################################
    def test_calc_01(self):
        dicData = {
            "__func_globals__": {
                "eval": "$L{$bool{$!{%0, true, false}}}",
                "T": "$L{%0%~1}",
                "F": "$L{%~0%1}",
                "and": "$L{$!{$!{%0, %1}, %0}}",
            },
            "result_T-F": "${eval, ${and, ${T}, ${F}}}",
            "result_T-T": "${eval, ${and, ${T}, ${T}}}",
        }

        xResult: dict = ison.run.Run(xData=dicData, bStripVars=False)

        assert xResult["result_T-F"] == False
        assert xResult["result_T-T"] == True

    # enddef


# endclass
