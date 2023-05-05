#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \dev\test_01.py
# Created Date: Monday, February 28th 2022, 10:47:19 am
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

from pathlib import Path
import ison

dicData = {
    "__globals__": {
        # evaluation function to see the effect
        "f": "$L{$sum{%0, 1}}",
        "zero": "$L{%~0%1}",  # same as FALSE
        # The successor operator
        "succ": "$L{$!{%1, $!{$!{%0, %1}, %2}}}",
    },
    "result": {
        # This shows the lambda function result
        "func": "${succ, ${zero}}",
        # # The evaluated result
        # "eval": "${succ, ${zero}, ${f}, 0}",
        # # This demonstrates the effect of applying the
        # # evaluation function twice
        # "x": "${f, ${f, 0}}"
    },
}

xResult = ison.run.Run(xData=dicData, bStripVars=False)

pathFile = Path(__file__)
ison.util.io.SaveJson(
    pathFile.parent / f"_out-{pathFile.stem}.json", xResult, iIndent=4
)
