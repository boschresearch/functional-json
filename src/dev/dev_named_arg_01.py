#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \dev_named_arg_01.py
# Created Date: Tuesday, April 25th 2023, 9:04:01 am
# Author: Christian Perwass
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
    "__globals__": {"lKeys": ["a", "b", "c", "d"], "lValues": [1, 2, 3]},
    "result": "$write{test.json, $lKeys, json-indent=4}",
}

xResult = ison.run.Run(xData=dicData, bStripVars=False)

print(xResult)

pathFile = Path(__file__)
ison.util.io.SaveJson(pathFile.parent / f"_out-{pathFile.stem}.json", xResult, iIndent=4)
