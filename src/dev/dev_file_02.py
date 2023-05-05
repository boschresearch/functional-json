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

import sys
from pathlib import Path

pathFile = Path(__file__)
sPathIson = pathFile.parent.parent.as_posix()
if sPathIson not in sys.path:
    sys.path.insert(0, sPathIson)
# endif

import ison

print(ison.__file__)

dicData = {
    "__locals__": {
        "sPath": "./*.py",
        "lDir": "$dir{${sPath}}",
        "lFiles": "$!foreach{$L{${$path.parts{%0}:-1}}, *${lDir}}",
        "lFiles2": "$!foreach{$L{$path.name{%0}}, *${lDir}}",
        # "lInfo": "$!foreach{$L{$path.info{%0}}, *${lDir}}"
    },
    "result": "${lFiles}",
    "result2": "${lFiles2}",
    # "info": "${lInfo}"
}

xResult = ison.run.Run(xData=dicData, sImportPath=pathFile.parent.as_posix())

print(xResult)
