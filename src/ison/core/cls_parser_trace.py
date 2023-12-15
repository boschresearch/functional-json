#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \cls_parser_trace.py
# Created Date: Tuesday, September 27th 2022, 10:28:05 am
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
###

import enum
from typing import Callable, NamedTuple, Optional


####################################################################################
class EParseContext(enum.Enum):
    NONE = enum.auto()
    PRE = enum.auto()
    RTV = enum.auto()
    GLO = enum.auto()
    LOC = enum.auto()
    FGLO = enum.auto()
    FLOC = enum.auto()
    DICT = enum.auto()
    DICT_EL = enum.auto()
    LIST = enum.auto()
    LIST_EL = enum.auto()
    PLAT = enum.auto()
    PLAT_DATA = enum.auto()
    REF_PATH = enum.auto()
    FUNC = enum.auto()
    INC = enum.auto()
    ARG = enum.auto()
    VAR = enum.auto()
    MATCH = enum.auto()


# endclass enum


####################################################################################
class CParseContextElement(NamedTuple):
    eContext: EParseContext = EParseContext.NONE
    sValue: str = ""
    lData: list = None
    iData: int = None


# endclass


####################################################################################
class EWarningType(enum.Enum):
    NONE = enum.auto()
    UNDEF_VAR = enum.auto()


# endclass


####################################################################################
class CWarning:
    def __init__(self, *, _eType: EWarningType, _sKey: str, _sCtx: str = None, _sShortCtx: str = None):
        self.eType = _eType
        self.sKey = _sKey
        self.sCtx = _sCtx
        self.sShortCtx = _sShortCtx

    # enddef

    @property
    def sMessage(self):
        if self.eType == EWarningType.UNDEF_VAR:
            sMsg = f"Undefined variable '{self.sKey}'"
        else:
            sMsg = "Unknown warning type"
        # endif

        if isinstance(self.sShortCtx, str) and len(self.sShortCtx) > 0:
            sMsg += f": {self.sShortCtx}"
        # endif

        if isinstance(self.sCtx, str) and len(self.sCtx) > 0:
            sMsg += "\n" + self.sCtx
        # endif

        return sMsg

    # enddef


# endclass


####################################################################################
class CWarningList:
    def __init__(self):
        self.dicWarnType: dict[EWarningType] = {}

    # enddef

    def Clear(self):
        self.dicWarnType = {}

    # enddef

    def Add(self, _warnX: CWarning):
        dicWarn = self.dicWarnType.get(_warnX.eType)
        if dicWarn is None:
            dicWarn = self.dicWarnType[_warnX.eType] = {}
        # endif
        if _warnX.sKey not in dicWarn:
            dicWarn[_warnX.sKey] = _warnX
        # endif

    # enddef

    def FilterList(self, _dicExclude: dict[EWarningType, list[str]]) -> "CWarningList":
        xNewList = CWarningList()
        for eType, dicWarn in self.dicWarnType.items():
            lExcludeKeys: list[str] = []
            if eType in _dicExclude:
                lExcludeKeys = _dicExclude[eType]
            # endif
            for sKey, xWarn in dicWarn.items():
                if sKey in lExcludeKeys:
                    continue
                # endif
                xNewList.Add(xWarn)
            # endfor
        # endfor

        return xNewList

    # enddef

    def ToString(self, _dicExclude: Optional[dict[EWarningType, list[str]]] = None) -> str:
        sMsg = ""
        for eType in self.dicWarnType:
            lExcludeKeys: list[str] = []
            if isinstance(_dicExclude, dict) and eType in _dicExclude:
                lExcludeKeys = _dicExclude[eType]
            # endif

            dicWarn: dict[str] = self.dicWarnType[eType]
            for sKey in dicWarn:
                if sKey in lExcludeKeys:
                    continue
                # endif
                warnX: CWarning = dicWarn[sKey]
                sMsg += warnX.sMessage + "\n"
            # endfor
        # endfor
        return sMsg

    # enddef

    def __str__(self):
        return self.ToString()

    # enddef

    @property
    def bHasWarnings(self):
        return len(self.dicWarnType) > 0

    # enddef


# endclass CWarningList
