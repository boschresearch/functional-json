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
    def test_locals_01(self):
        dicData = {
            "__func_globals__": {
                "fX": "Hello",
            },
            "__globals__": {
                "fA": "${fB}",
                "fB": 1,
            },
            "mTest": {
                "__locals__": {
                    "fA": "${fB}",
                    "fB": "Hello",
                },
                "x": "${fA}",
            },
            "x": "${fA}",
        }

        xResult: dict = ison.run.Run(xData=dicData, bStripVars=False)

        assert xResult["x"] == 1
        assert xResult["mTest"]["x"] == "Hello"
        assert xResult["__globals__"]["fA"] == 1

    # enddef

    ################################################################################
    def test_eval_01(self):
        dicData = {
            "__func_globals__": {
                "fRand": "$rand.uniform{0, 1}",
            },
            "__globals__": {
                "fA": "${fRand}",
                "fB": {"x": "${fRand}", "y": "${X}"},
                "fA2": "${fA}",
                "fB2": "${fB:y}",
            },
            "fA2": "${fA2}",
            "fB2": "${fB2}",
            "fA": "${fA}",
            "fB": "${fB}",
            "fC": "${fRand}",
        }

        xResult: dict = ison.run.Run(xData=dicData, bStripVars=False)

        assert (
            xResult["__func_globals__"]["fRand"] == dicData["__func_globals__"]["fRand"]
        )
        assert xResult["__globals__"]["fA"] == xResult["__globals__"]["fA2"]
        assert xResult["__globals__"]["fA"] != xResult["__globals__"]["fB"]["x"]
        assert xResult["fC"] != xResult["fA"]
        assert xResult["fC"] != xResult["fB"]

    # enddef


# endclass
