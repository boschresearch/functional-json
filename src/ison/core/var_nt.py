#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \var_nt.py
# Created Date: Tuesday, April 25th 2023, 8:47:52 am
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


def Create(sKey: str, xData) -> tuple:
    return ("@NT", {sKey: xData})


# enddef


def Empty() -> tuple:
    return ("@NT", {})


# enddef


def Add(tNt: tuple, sKey: str, xData) -> tuple:
    tNt[1][sKey] = xData
    return tNt


# enddef


def Remove(tNt: tuple, sKey: str) -> tuple:
    dicData = tNt[1]
    if sKey in dicData:
        del dicData[sKey]
    # endif
    return tNt


# enddef


def IsEmpty(tNt: tuple) -> bool:
    if not IsValid(tNt):
        return True
    # endif
    return len(tNt[1]) == 0


# enddef


def IsValid(xVar) -> bool:
    return isinstance(xVar, tuple) and len(xVar) == 2 and xVar[0] == "@NT" and isinstance(xVar[1], dict)


# enddef


def GetData(xVar, bDoRaise: bool = False) -> dict:
    if not IsValid(xVar):
        if bDoRaise is True:
            raise RuntimeError("Variable is not a named tuple")
        else:
            return None
        # endif
    # endif

    return xVar[1]


# endif
