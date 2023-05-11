#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: /compositor.py
# Created Date: Thursday, October 22nd 2020, 4:26:28 pm
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

import json

from ..core.cls_parser_error import CParserError_Message, CParserError_ProcArgStr


################################################################################
# Find balanced closed element
# The element of _sValue at _iStartIdx defines the start character.
# _sEndChar defines the end character.
# If a balanced end character cannot be found, None is returned.
def FindBalancedChar(_sValue, _iStartIdx, _sEndChar):
    iStartCnt = 1
    sStartChar = _sValue[_iStartIdx]

    iIdx = _iStartIdx + 1
    iCnt = len(_sValue)
    while iIdx < iCnt:
        sChar = _sValue[iIdx]
        if sChar == _sEndChar:
            iStartCnt -= 1
            if iStartCnt == 0:
                break
            # endif
        elif sChar == sStartChar:
            iStartCnt += 1
        # endif
        iIdx += 1
    # endwhile

    if iStartCnt != 0:
        raise CParserError_Message(
            sMsg="Closing '{}' missing: {}".format(_sEndChar, HighlightStringPart(_sValue, _iStartIdx, _iStartIdx + 1))
        )
    # endif

    return iIdx


# enddef


################################################################################
# Split Arguments in string accounting for brackets.
# For example, the string "a, (b, c), d" is split into ["a", "(b, c)", "d"].
# All types of brackets are taken into account "()", "[]", "{}"
def SplitArgs(_sValue, sSplitChar=","):
    lArgs = []
    sOpen = "([{"
    sClose = ")]}"
    lBrkCnt = [0, 0, 0]

    sStringChars = "'`\""
    sActStrChar = None

    lEndIdx = []
    iStart = 0
    iIdx = 0
    sChar = None
    for iIdx in range(len(_sValue)):
        sPrevChar = sChar
        sChar = _sValue[iIdx]
        if sChar in sStringChars and sPrevChar != "\\":
            if sActStrChar is None:
                sActStrChar = sChar
            elif sActStrChar == sChar:
                sActStrChar = None
            # endif
        # endif

        if sActStrChar is not None:
            continue
        # endif

        iOpenIdx = sOpen.find(sChar)
        iCloseIdx = sClose.find(sChar)

        if sChar == sSplitChar and all((x == 0 for x in lBrkCnt)):
            sArg = _sValue[iStart:iIdx].strip()
            lArgs.append(sArg)
            lEndIdx.append(iIdx + 1)
            iStart = iIdx + 1

        elif iOpenIdx >= 0:
            lBrkCnt[iOpenIdx] += 1

        elif iCloseIdx >= 0:
            if lBrkCnt[iCloseIdx] == 0:
                raise CParserError_Message(
                    sMsg="Unexpected close bracket '{0}' at index {1} in: {2}>>{3}<<{4}".format(
                        sClose[iCloseIdx],
                        iIdx,
                        _sValue[0:iIdx],
                        _sValue[iIdx],
                        _sValue[iIdx + 1 :],
                    )
                )
            # endif
            lBrkCnt[iCloseIdx] -= 1
        # endif
    # endfor

    if sActStrChar is not None:
        raise CParserError_Message(sMsg="Missing closed string symbol >{0}< in: {1}".format(sActStrChar, _sValue))
    # endif

    iOpenIdx = -1
    if lBrkCnt[0] > 0:
        iOpenIdx = 0
    elif lBrkCnt[1] > 0:
        iOpenIdx = 1
    elif lBrkCnt[2] > 0:
        iOpenIdx = 2
    # endif
    if iOpenIdx >= 0:
        raise CParserError_Message(sMsg="Missing closed bracket '{0}' in: {1}".format(sClose[iOpenIdx], _sValue))
    # endif

    sArg = _sValue[iStart:].strip()
    lArgs.append(sArg)
    lEndIdx.append(len(_sValue))

    return lArgs, lEndIdx


# enddef


################################################################################
# Split a variable path, honoring embedded functions.
# For example, "id:!ref(id:hello:name):value" is split into ["id", "!ref(id:hello:name)", "value"]
def SplitVarPath(_sPath):
    lArgs, lEndIdx = SplitArgs(_sPath, sSplitChar=":")
    return lArgs


# enddef


################################################################################
# Get the list of variables in the given string, supporting nested variables.
# For example, "$foo{$dict_path_list{cameras}, 'test} - $fab{cameras}" returns:
# [
#   {"sFunc": "foo", "lArgs": ["$dict_path_list{cameras}", "'test"], "iStart": 0, "iEnd": 37 },
#   {"sFunc": "fab", "lArgs": ["cameras"], "iStart": 40, "iEnd": 52}
# ]
def GetVarMatchList(_sValue, _reVarStart, *, lSingleArgsFuncs=[]):
    lMatch = []
    iSearchIdx = 0
    while True:
        xMatch = _reVarStart.search(_sValue, iSearchIdx)
        if xMatch is None:
            break
        # endif

        sFunc = xMatch.group("func")
        if sFunc is not None:
            iEnd = FindBalancedChar(_sValue, xMatch.end() - 1, "}")

            sMatch = _sValue[xMatch.start() : iEnd + 1]
            sArgs = _sValue[xMatch.end() : iEnd]

            if sFunc in lSingleArgsFuncs:
                lArgs = [sArgs]
            else:
                try:
                    lArgs, lEndIdx = SplitArgs(sArgs)
                except Exception as xEx:
                    raise CParserError_ProcArgStr(sString=sArgs, xChildEx=xEx)
                # endtry
            # endif

        else:
            # pure variable reference, e.g. "$var"
            # use reference function
            sFunc = ""
            lArgs = [xMatch.group("var")]
            iEnd = xMatch.end() - 1
            sMatch = _sValue[xMatch.start() : xMatch.end()]
        # endif

        lMatch.append(
            {
                "sFunc": sFunc,
                "lArgs": lArgs,
                "iStart": xMatch.start(),
                "iEnd": iEnd + 1,
                "sMatch": sMatch,
            }
        )

        iSearchIdx = iEnd + 1
    # endwhile

    return lMatch


# enddef


################################################################################
def HighlightElementString(_lData, _iIdx, _sSep):
    lStr = []
    for i, xVal in enumerate(_lData):
        if i == _iIdx:
            lStr.append(">>{0}<<".format(str(xVal)))
        else:
            lStr.append(str(xVal))
        # endif
    # endfor

    return _sSep.join(lStr)


# enddef


################################################################################
def HighlightStringPart(_sString, _iStart, _iEnd):
    return _sString[0:_iStart] + ">>" + _sString[_iStart:_iEnd] + "<<" + _sString[_iEnd:]


# enddef


################################################################################
def ToString(_xValue, *, iIndent=None):
    if isinstance(_xValue, dict) or isinstance(_xValue, list) or isinstance(_xValue, tuple):
        return json.dumps(_xValue, indent=iIndent)
    else:
        return str(_xValue)
    # endif


# enddef


################################################################################
# Strip a string off start and end string char and convert \` to `
def StripLiteralString(_sValue):
    return StripString(_sValue, "`")


# enddef


################################################################################
# Strip a string off start and end string char and convert \` to `
def StripString(_sValue, _sChar):
    sEscChar = f"\\{_sChar}"

    if not isinstance(_sValue, str) or len(_sValue) < 2:
        return _sValue
    # endif

    if _sValue.startswith(sEscChar) and _sValue.endswith(sEscChar):
        sInner = _sValue[2:-2]
        sValue = f"{_sChar}{sInner}{_sChar}"
    elif _sValue[0] != _sChar:
        return _sValue
    else:
        iClosedIdx = FindBalancedChar(_sValue, 0, _sChar)
        if iClosedIdx + 1 == len(_sValue):
            sValue = _sValue[1:iClosedIdx]
            sValue = sValue.replace(f"\\{_sChar}", _sChar)

        else:
            sValue = _sValue
        # endif
    # endif

    return sValue


# enddef
