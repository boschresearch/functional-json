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

print(ison.__file__)

dicData = {
    "__runtime_vars__": {
        "file": "$read{test-01.json}",
    },
    "value": "$hello -> ${file:data:a}",
}

dicConst = {
    "hello": 1,
}

xResult = ison.run.Run(
    xData=dicData, dicConstVars=dicConst, sImportPath=Path(__file__).parent.as_posix(), bStripVars=False
)

print(xResult)

# pathFile = Path(__file__)
# ison.util.io.SaveJson(pathFile.parent / f"_out-{pathFile.stem}.json", xResult, iIndent=4)
