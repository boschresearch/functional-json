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

import ison

dicData = {
    "__func_globals__": {
        # "JustDict": "$L{%0}",
        "AsString": "$L{%0:%1}",
        # "FromDict": "$L{${%0:%1}}",
    },
    "__locals__": {
        "dicA": {
            "a": 1,
            "b": 2,
        }
    },

    # "result 1": "${JustDict, $dicA}",
    "result 2": "${AsString, $dicA, b}",
    # "result 3": "${FromDict, $dicA, b}",
}

dicResult = ison.run.Run(xData=dicData)
print(ison.run.ToString(dicResult))
