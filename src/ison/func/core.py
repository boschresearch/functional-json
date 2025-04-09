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

import math
import re
import json

from ..util import text, convert
from ..core import lambda_parser as lp
from ..core.defines import reLiteralString
from ..core import var_nt
from ..core.cls_parser_error import (
    CParserError,
    CParserError_Message,
    CParserError_DictSel,
    CParserError_ListSel,
    CParserError_ProcArgStr,
    CParserError_ProcFunc,
    CParserError_ProcFuncArgs,
    CParserError_ProcKey,
    CParserError_ProcLambda,
    CParserError_ProcLambdaArgs,
    CParserError_ProcRefPath,
    CParserError_ProcStr,
    CParserError_StrMatch,
    CParserError_KeyStrMatch,
    CParserError_FuncMessage,
)


def tooltip(sTooltip):
    def inner(func):
        func.tooltip = sTooltip
        return func

    return inner


g_reStrFmt = re.compile(r"^(?P<sign>[-+])?(?P<zero>0)?(?P<len>\d+)(\.(?P<prec>\d+))?(?P<type>[dxXeEfFgG])\s*$")


################################################################################
@tooltip("Variable lookup")
def Reference(_xParser, _lArgs, _lArgIsProc, *, sFuncName):
    # This function receives unprocessed argument by default

    iArgCnt = len(_lArgs)

    if iArgCnt < 1:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="Variable reference expects at least 1 argument but {0} were given".format(iArgCnt),
        )
    # endif

    bProcessPath = None
    xArg = _lArgs[0]
    # Due to the function $*{}, the argument can be a structure
    # instead of a string. In this case, we treat it, as if the
    # structure had been returned from a reference lookup.
    if isinstance(xArg, str):
        bProcessPath = True

        try:
            # Split the match by ':'
            lPath = text.SplitVarPath(xArg)

            # process the elements of path
            lVarData, lVarIsProc = _xParser._ProcessArgs(lPath)
        except Exception as xEx:
            raise CParserError_ProcArgStr(sString=xArg, sContext="Reference argument", xChildEx=xEx)
        # endtry

        # if not all elements of the path could be processed,
        # return None.
        if not all((x for x in lVarIsProc)):
            return None, False
        # endif

    else:
        bProcessPath = False
        xFunc = xArg
    # endif

    if iArgCnt > 1:
        try:
            lLamPar, lLamParProc = _xParser._ProcessArgs(_lArgs[1:])
        except Exception as xEx:
            raise CParserError_ProcLambdaArgs(xLambda=xArg, lArgs=_lArgs[1:], xChildEx=xEx)
        # endtry

        if not all((x for x in lLamParProc)):
            return None, False
        # endif
    # endif

    bLiteral = False

    if bProcessPath is True:
        # test whether the first element of a path is not a string
        if not isinstance(lVarData[0], str):
            # use the first element of the path as the object
            try:
                xFunc, bLiteral = _xParser.ProcessRefPath(lVarData[0], lVarData[1:], 0)
            except Exception as xEx:
                sSrc = f"the result of '{lPath[0]}'"
                raise CParserError_ProcRefPath(sContext=sSrc, lMatch=lVarData[1:], iMatchIdx=0, xChildEx=xEx)
            # endtry

        else:
            # Obtain the referenced element in the variable data
            try:
                xFunc, bLiteral = _xParser.ProcessRefPath(_xParser.GetVarData(), lVarData, 0)
            except Exception as xEx:
                raise CParserError_ProcRefPath(sContext="variables", lMatch=lVarData, iMatchIdx=0, xChildEx=xEx)
            # endtry
        # endif
    # endif

    if iArgCnt > 1:

        def SubProcess(_xBody):
            xResult, bIsProc = _xParser.InnerProcess(_xBody)
            return xResult

        # enddef

        if bLiteral is False:
            xFunc, bLiteral = _xParser.InnerProcess(xFunc)
        # endif

        try:
            xFunc = lp.Parse(xFunc, lLamPar, funcProcess=SubProcess)
        except Exception as xEx:
            raise CParserError_ProcLambda(xLambda=xFunc, lArgs=lLamPar, xChildEx=xEx)
        # endtry
    # endif

    return xFunc, bLiteral


# enddef


################################################################################
@tooltip("Convert all `/` in a path by `:`, so that it becomes an ison variable path")
def ToRefPath(_xParser, _lArgs, _lArgIsProc, *, sFuncName):
    if not all(_lArgIsProc):
        return None, False
    # endif

    iArgCnt = len(_lArgs)

    if iArgCnt != 1:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="Convert to reference path function reequires exactly one argument, {0} are given".format(iArgCnt),
        )
    # endif

    xResult = _lArgs[0].replace("/", ":")

    return xResult, False


# enddef


################################################################################
@tooltip("Convert argument to json string")
def AsString(_xParser, _lArgs, _lArgIsProc, *, sFuncName):
    iArgCnt = len(_lArgs)

    if iArgCnt != 1:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="A string object must have exactly 1 argument but {0} were given".format(iArgCnt),
        )
    # endif

    sArg = lp.ConvertLambdaToJsonStrings(_lArgs[0], _bInStringContext=True)
    xResult = f'"{sArg}"'

    return xResult, True


# enddef


################################################################################
@tooltip("Convert argument to json string")
def AsStringBackQuote(_xParser, _lArgs, _lArgIsProc, *, sFuncName):
    iArgCnt = len(_lArgs)

    if iArgCnt != 1:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="A string object must have exactly 1 argument but {0} were given".format(iArgCnt),
        )
    # endif

    sArg = lp.ConvertLambdaToJsonStrings(_lArgs[0], _bInStringContext=True)
    xResult = f"`{sArg}`"

    return xResult, True


# enddef


################################################################################
@tooltip("Explicit lambda call: first argument is the function, the rest are list of arguments")
def LambdaCall(_xParser, _lArgs, _lArgIsProc, *, sFuncName):
    iArgCnt = len(_lArgs)

    if iArgCnt < 1:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="A lambda call expects at least 1 argument but {0} were given".format(iArgCnt),
        )
    # endif

    def SubProcess(_xBody):
        xResult, bIsProc = _xParser.InnerProcess(_xBody)
        return xResult

    # enddef

    xFunc = _lArgs[0]
    xResult = lp.Parse(xFunc, _lArgs[1:], funcProcess=SubProcess)

    return xResult, False


# enddef


################################################################################
@tooltip("Execute lambda function (first argument) for all remaining arguments")
def LambdaCall_ForEach_Arg(_xParser, _lArgs, _lArgIsProc, *, sFuncName):
    iArgCnt = len(_lArgs)

    if iArgCnt < 1:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="Lambda call 'for each' expects at least 1 argument but {0} were given".format(iArgCnt),
        )
    # endif

    def SubProcess(_xBody):
        xResult, bIsProc = _xParser.InnerProcess(_xBody)
        return xResult

    # enddef

    lResults = []
    xFunc = _lArgs[0]
    lFuncArgs = _lArgs[1:]

    tIsNamedTuple = tuple(var_nt.IsValid(x) for x in lFuncArgs)
    bAllNamedArgs = all(tIsNamedTuple)
    if any(tIsNamedTuple) is True and bAllNamedArgs is False:
        raise CParserError_FuncMessage(
            sFunc=sFuncName, sMsg="You cannot mix named and unnamed arguments in 'for each' lambda call"
        )
    # endif

    if bAllNamedArgs is True:
        lKeys: list[str] = []
        lValueLists: list[list] = []

        iMinValueCnt: int = None
        for tFuncArg in lFuncArgs:
            dicNT: dict = tFuncArg[1]
            for sKey in dicNT:
                lKeys.append(sKey)
                xValue = dicNT[sKey]
                if isinstance(xValue, tuple):
                    lValueLists.append(list(xValue))
                    iValueCnt = len(xValue)
                    if iMinValueCnt is None:
                        iMinValueCnt = iValueCnt
                    else:
                        iMinValueCnt = min(iMinValueCnt, iValueCnt)
                    # endif
                else:
                    lValueLists.append([xValue])
                # endif
            # endfor
        # endfor

        if iMinValueCnt is None:
            iMinValueCnt = 1
        # endif

        for iIterIdx in range(iMinValueCnt):
            lNewArg = []
            for iKeyIdx, sKey in enumerate(lKeys):
                lKeyValues = lValueLists[iKeyIdx]
                if len(lKeyValues) == 1:
                    xValue = lKeyValues[0]
                else:
                    xValue = lKeyValues[iIterIdx]
                # endif
                lNewArg.append(var_nt.Create(sKey, xValue))
                # lNewArg.append(f"{sKey}={xValue}")
            # endfor

            xResult = lp.Parse(xFunc, lNewArg, funcProcess=SubProcess)
            lResults.append(xResult)
        # endfor

    else:
        for xArg in _lArgs[1:]:
            lNewArg = None
            if isinstance(xArg, tuple):
                lNewArg = list(xArg)
            else:
                lNewArg = [xArg]
            # endif
            xResult = lp.Parse(xFunc, lNewArg, funcProcess=SubProcess)

            lResults.append(xResult)
        # endfor
    # endif

    return lResults, False


# enddef


################################################################################
@tooltip(
    "Use lambda function (first argument) to test each of the remaining arguments. "
    "Only those elements are returned where lambda function returns true"
)
def LambdaCall_ForEach_Where(_xParser, _lArgs, _lArgIsProc, *, sFuncName):
    iArgCnt = len(_lArgs)

    if iArgCnt < 1:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="Lambda call 'select' expects at least 1 argument but {0} were given".format(iArgCnt),
        )
    # endif

    def SubProcess(_xBody):
        xResult, bIsProc = _xParser.InnerProcess(_xBody)
        return xResult

    # enddef

    lResults = []
    xFunc = _lArgs[0]
    for xArg in _lArgs[1:]:
        lNewArg = None
        if isinstance(xArg, tuple):
            lNewArg = list(xArg)
        else:
            lNewArg = [xArg]
        # endif
        xResult = lp.Parse(xFunc, lNewArg, funcProcess=SubProcess)
        if isinstance(xResult, bool) and xResult is True:
            lResults.append(xArg)
        # endif
    # endfor

    return lResults, False


# enddef


################################################################################
@tooltip("Define lambda function")
def Lambda(_xParser, _lArgs, _lArgIsProc, *, sFuncName):
    iArgCnt = len(_lArgs)

    if iArgCnt != 1:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="Lambda function definitions must have exactly 1 argument but {0} were given".format(iArgCnt),
        )
    # endif

    xResult = "$L{{{0}}}".format(_lArgs[0])

    return xResult, True


# enddef


################################################################################
@tooltip("Define data structure as lambda function")
def LambdaDef(_xParser, _lArgs, _lArgIsProc, *, sFuncName):
    iArgCnt = len(_lArgs)

    if iArgCnt != 1:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="Lambda function definitions must have exactly 1 argument but {0} were given".format(iArgCnt),
        )
    # endif

    if not isinstance(_lArgs[0], str):
        raise CParserError_FuncMessage(sFunc=sFuncName, sMsg="Function 'L*': argument has to be a string")
    # endif

    xBody, bIsLiteral = Reference(_xParser, _lArgs, [False], sFuncName=sFuncName)
    sBody = lp.ToLambdaString(xBody)

    xResult = "$L{{$*{{^{0}}}}}".format(sBody)

    return xResult, True


# enddef


################################################################################
@tooltip("Convert string argument to data object")
def ToStruct(_xParser, _lArgs, _lArgIsProc, *, sFuncName):
    if not all(_lArgIsProc):
        return None, False
    # endif

    iArgCnt = len(_lArgs)

    if iArgCnt != 1:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="Structure unpacking must have exactly 1 argument but {0} were given".format(iArgCnt),
        )
    # endif

    sArg = _lArgs[0]
    if not isinstance(sArg, str):
        raise CParserError_FuncMessage(sFunc=sFuncName, sMsg="Argument to function '*' must be a string")
    # endif

    # Due to the replacement in Lambda functions, there may be mulitply nested strings.
    # To handle this, the lambda parser packs strings in arguments into function blocks $S{}.
    # The top level string blocks need to be replaced by quotes again here.
    try:
        sNewArg = re.sub(reLiteralString, r"$S{\1}", sArg)

        xResult = lp.ToLambdaObject(sNewArg)
    except Exception as xEx:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="Error converting string to structure: {}\n{}".format(sArg, str(xEx)),
        )
    # enddef

    return xResult, False


# enddef


################################################################################
@tooltip("Convert argument to json string")
def ToJson(_xParser, _lArgs, _lArgIsProc, *, sFuncName):
    if not all(_lArgIsProc):
        return None, False
    # endif

    iArgCnt = len(_lArgs)

    if iArgCnt != 1:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="Conversion to json string must have exactly 1 argument but {0} were given".format(iArgCnt),
        )
    # endif

    xValue = _lArgs[0]

    if isinstance(xValue, dict) or isinstance(xValue, list):
        xResult = json.dumps(xValue, indent=4)
    else:
        xResult = str(xValue)
    # endif

    return xResult, False


# enddef


################################################################################
@tooltip("Convert argument to string with optional formatting")
def ToString(_xParser, _lArgs, _lArgIsProc, *, sFuncName):
    global g_reStrFmt

    if not all(_lArgIsProc):
        return None, False
    # endif

    iArgCnt = len(_lArgs)

    if iArgCnt < 1 or iArgCnt > 2:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="Conversion to string must have 1 or 2 arguments but {0} were given".format(iArgCnt),
        )
    # endif

    xValue = _lArgs[0]

    if iArgCnt == 1:
        xResult = str(xValue)
        # if isinstance(xValue, dict) or isinstance(xValue, list):
        #     xResult = json.dumps(xValue, indent=4)
        # else:
        #     xResult = str(xValue)
        # # endif

    else:
        sFormat = _lArgs[1]
        if not isinstance(sFormat, str):
            raise CParserError_FuncMessage(sFunc=sFuncName, sMsg="Second argument must be a formatting string")
        # endif

        xMatch = g_reStrFmt.match(sFormat)
        if xMatch is None:
            raise CParserError_FuncMessage(sFunc=sFuncName, sMSg="Invalid format string '{}'".format(sFormat))
        # endif

        sType = xMatch.group("type")
        if sType in ["d", "x", "X"] and xMatch.group("prec") is not None:
            raise CParserError_FuncMessage(
                sFunc=sFuncName,
                sMsg="Precision not allowed in format string for integer values",
            )
        # endif

        try:
            if sType in ["d", "x", "X"]:
                xValue = convert.ToInt(xValue)
            elif sType in ["e", "E", "f", "F", "g", "G"]:
                xValue = convert.ToFloat(xValue)
            else:
                raise RuntimeError("Unsupported format type '{}'".format(sType))
            # endif
        except Exception as xEx:
            raise CParserError_FuncMessage(
                sFunc=sFuncName,
                sMsg="Error converting value to format type",
                xChildEx=xEx,
            )
        # endtry

        try:
            xResult = "{{:{}}}".format(sFormat).format(xValue)
        except Exception as xEx:
            raise CParserError_FuncMessage(sFunc=sFuncName, sMsg="Error formatting value", xChildEx=xEx)
        # endtry
    # endif

    return xResult, False


# enddef


################################################################################
@tooltip("Enumerate list. Returns list of tuples each with index and data element")
def Enumerate(_xParser, _lArgs, _lArgIsProc, *, sFuncName):
    if not all(_lArgIsProc):
        return None, False
    # endif

    iArgCnt = len(_lArgs)

    if iArgCnt != 1:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="The enumerate function must have exactly 1 argument but {0} were given".format(iArgCnt),
        )
    # endif

    lArg = _lArgs[0]
    if not isinstance(lArg, list):
        raise CParserError_FuncMessage(sFunc=sFuncName, sMsg="Argument to function 'enumerate' must be a list")
    # endif

    lResult = []
    for iIdx, xArg in enumerate(lArg):
        lResult.append((iIdx, xArg))
    # endfor

    return lResult, False


# enddef


################################################################################
@tooltip(
    "Combines corresponding elements of set of lists to a list of tuples, each with one value from each input list, i.e. list(zip(lArg1,lArg2,...)"
)
def Group(_xParser, _lArgs, _lArgIsProc, *, sFuncName):
    if not all(_lArgIsProc):
        return None, False
    # endif

    iArgCnt = len(_lArgs)

    if iArgCnt == 0:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="Expect at least 1 argument but {0} were given".format(iArgCnt),
        )
    # endif

    for iIdx, xArg in enumerate(_lArgs):
        if not isinstance(xArg, list):
            raise CParserError_FuncMessage(sFunc=sFuncName, sMsg=f"Argument {(iIdx+1)} must be a list")
        # endif
    # endfor

    lResult = list(zip(*_lArgs))

    return lResult, False


# enddef


################################################################################
@tooltip("Union of lists or dictionaries")
def ToUnion(_xParser, _lArgs, _lArgIsProc, *, sFuncName):
    if not all(_lArgIsProc):
        return None, False
    # endif

    iArgCnt = len(_lArgs)

    if iArgCnt < 1:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="The union function must have at least 1 argument but {0} were given".format(iArgCnt),
        )
    # endif

    xResult = None

    # if all arguments are dictionaries, then combine these
    # in a single dictionary using sequential update().
    if all((isinstance(x, dict) for x in _lArgs)):
        xResult = {}
        for dicSub in _lArgs:
            xResult.update(dicSub)
        # endfor

    # otherwise combine all arguments in a list.
    # All arguments that are lists themselves are unwrapped, i.e.
    # their elements are appended to the union list.
    else:
        xResult = []
        for xArg in _lArgs:
            if isinstance(xArg, list) or isinstance(xArg, tuple):
                xResult.extend(xArg)
            else:
                xResult.append(xArg)
            # endif
        # endfor
    # endif

    return xResult, False


# enddef


################################################################################
@tooltip(
    "Generate list of integers start value (argument 1) to and including end value (argument 2) with step size (argument 3). "
    "If only single argument is given, then a list from zero to the argument minus one is returned"
)
def ToRange(_xParser, _lArgs, _lArgIsProc, *, sFuncName):
    if not all(_lArgIsProc):
        return None, False
    # endif

    iArgCnt = len(_lArgs)

    if iArgCnt < 1 or iArgCnt > 3:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="The range function must have 1, 2 or 3 arguments but {0} were given".format(iArgCnt),
        )
    # endif

    try:
        iStart = int(_lArgs[0])
    except Exception as xEx:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="Function '{}': argument 1 cannot be converted to integer".format(sFuncName),
            xChildEx=xEx,
        )
    # endtry

    lResult = None
    if iArgCnt == 1:
        lResult = list(range(iStart))

    elif iArgCnt >= 2:
        try:
            iEnd = convert.ToInt(_lArgs[1])
        except Exception as xEx:
            raise CParserError_FuncMessage(
                sFunc=sFuncName,
                sMsg="Function '{}': argument 2 cannot be converted to integer".format(sFuncName),
                xChildEx=xEx,
            )
        # endtry

        iStep = 1
        if iArgCnt >= 3:
            try:
                iStep = convert.ToInt(_lArgs[2])
            except Exception as xEx:
                raise CParserError_FuncMessage(
                    sFunc=sFuncName,
                    sMsg="Function '{}': argument 3 cannot be converted to integer".format(sFuncName),
                    xChildEx=xEx,
                )
            # endtry
        # endif

        lResult = list(range(iStart, iEnd + 1, iStep))
    # endif

    return lResult, False


# enddef


################################################################################
@tooltip("Number of elements in a list or dictionary")
def Len(_xParser, _lArgs, _lArgIsProc, *, sFuncName):
    if not all(_lArgIsProc):
        return None, False
    # endif

    iArgCnt = len(_lArgs)

    if iArgCnt != 1:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="Expect exactly 1 argument but {0} were given".format(iArgCnt),
        )
    # endif

    xArg = _lArgs[0]
    if not isinstance(xArg, list) and not isinstance(xArg, dict):
        raise CParserError_FuncMessage(sFunc=sFuncName, sMsg="Argument must be a list")
    # endif

    lResult = len(xArg)

    return lResult, False


# enddef


################################################################################
@tooltip("Check all arguments for equality, returns boolean")
def TestEqual(_xParser, _lArgs, _lArgIsProc, *, sFuncName):
    if not all(_lArgIsProc):
        return None, False
    # endif

    iArgCnt = len(_lArgs)

    if iArgCnt < 2:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="The equality function must have at least 2 arguments but {0} were given".format(iArgCnt),
        )
    # endif

    lNewArgs = None
    if any((isinstance(x, float) for x in _lArgs)):
        try:
            lNewArgs = [float(x) for x in _lArgs]
        except Exception as xEx:
            raise CParserError_FuncMessage(
                sFunc=sFuncName,
                sMsg="Error converting list of comparison elements to 'float': {}".format(str(xEx)),
            )
        # endtry

    elif any((isinstance(x, int) for x in _lArgs)):
        try:
            lNewArgs = [int(x) for x in _lArgs]
        except Exception as xEx:
            raise CParserError_FuncMessage(
                sFunc=sFuncName,
                sMsg="Error converting list of comparison elements to 'int': {}".format(str(xEx)),
            )
        # endtry

    else:
        lNewArgs = _lArgs
    # endif

    xTest = lNewArgs[0]

    # Test wether all elements are of the same type
    if not all((isinstance(x, type(xTest)) for x in lNewArgs[1:])):
        return False, False
    # endif

    if isinstance(xTest, list) or isinstance(xTest, dict):
        raise CParserError_FuncMessage(sFunc=sFuncName, sMsg="Comparison of lists and dicts not implemented")
    # endif

    xResult = all((x == xTest for x in lNewArgs[1:]))

    return xResult, False


# enddef


################################################################################
@tooltip("Evaluate boolean AND of all arguments")
def BoolAnd(_xParser, _lArgs, _lArgIsProc, *, sFuncName):
    if not all(_lArgIsProc):
        return None, False
    # endif

    iArgCnt = len(_lArgs)

    if iArgCnt < 2:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="The boolean AND function must have at least 2 arguments but {0} were given".format(iArgCnt),
        )
    # endif

    bResult = True
    for xArg in _lArgs:
        if isinstance(xArg, float):
            if xArg == 0.0:
                bResult = False
                break
            # endif

        elif isinstance(xArg, int):
            if xArg == 0:
                bResult = False
                break

        elif isinstance(xArg, bool):
            if xArg is False:
                bResult = False
                break

        else:
            raise CParserError_FuncMessage(sFunc=sFuncName, sMsg="Invalid element type in 'AND' argument list")
        # endif
    # endfor

    return bResult, False


# enddef


################################################################################
@tooltip("Evaluate logical OR of all arguments")
def BoolOr(_xParser, _lArgs, _lArgIsProc, *, sFuncName):
    if not all(_lArgIsProc):
        return None, False
    # endif

    iArgCnt = len(_lArgs)

    if iArgCnt < 2:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="The boolean OR function must have at least 2 arguments but {0} were given".format(iArgCnt),
        )
    # endif

    bResult = False
    for xArg in _lArgs:
        if isinstance(xArg, str):
            iVal: int | None = convert.ToInt(xArg, bDoRaise=False)
            if iVal is not None and iVal != 0:
                bResult = True
                break
            bVal: bool = convert.ToBool(xArg)
            if bVal:
                bResult = True
                break
        else:
            raise CParserError_FuncMessage(sFunc=sFuncName, sMsg="Invalid element type in 'OR' argument list")
        # endif
    # endfor

    return bResult, False


# enddef


################################################################################
@tooltip("Evaluate logical NOT of all arguments")
def BoolNot(_xParser, _lArgs, _lArgIsProc, *, sFuncName):
    if not all(_lArgIsProc):
        return None, False
    # endif

    iArgCnt = len(_lArgs)

    if iArgCnt != 1:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="The boolean NOT function must have exactly 1 argument but {0} were given".format(iArgCnt),
        )
    # endif

    bResult = None
    xArg = _lArgs[0]
    if isinstance(xArg, float):
        bResult = xArg == 0.0

    elif isinstance(xArg, int):
        bResult = xArg == 0

    elif isinstance(xArg, bool):
        bResult = not xArg

    else:
        raise CParserError_FuncMessage(sFunc=sFuncName, sMsg=f"Invalid element type of 'NOT' argument: {xArg}")
    # endif

    return bResult, False


# enddef


################################################################################
def _DoToBool(_xValue):
    if isinstance(_xValue, dict):
        raise RuntimeError("Cannot convert dictionary to bool")
    # endif

    if isinstance(_xValue, list):
        xResult = [_DoToBool(x) for x in _xValue]

    else:
        xResult = convert.ToBool(_xValue)
    # endif

    return xResult


# endif
#


################################################################################
@tooltip("Convert argument to bool")
def ToBool(_xParser, _lArgs, _lArgIsProc, *, sFuncName):
    if not all(_lArgIsProc):
        return None, False
    # endif

    iArgCnt = len(_lArgs)

    if iArgCnt == 0:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="Expected at least 1 argument but {0} were given".format(iArgCnt),
        )
    # endif

    if iArgCnt == 1:
        xResult = _DoToBool(_lArgs[0])
    else:
        xResult = _DoToBool(_lArgs)
    # endif

    return xResult, False


# enddef


################################################################################
def _DoToInt(_xValue):
    if isinstance(_xValue, dict):
        raise RuntimeError("Cannot convert dictionary to int")
    # endif

    if isinstance(_xValue, list):
        xResult = [_DoToInt(x) for x in _xValue]

    else:
        xResult = convert.ToInt(_xValue)
    # endif

    return xResult


# endif


################################################################################
@tooltip("Convert argument to integer")
def ToInt(_xParser, _lArgs, _lArgIsProc, *, sFuncName):
    if not all(_lArgIsProc):
        return None, False
    # endif

    iArgCnt = len(_lArgs)

    if iArgCnt == 0:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="Expected at least 1 argument but {0} were given".format(iArgCnt),
        )
    # endif

    if iArgCnt == 1:
        xResult = _DoToInt(_lArgs[0])
    else:
        xResult = _DoToInt(_lArgs)
    # endif

    return xResult, False


# enddef


################################################################################
def _DoToFloat(_xValue):
    if isinstance(_xValue, dict):
        raise RuntimeError("Cannot convert dictionary to int")
    # endif

    if isinstance(_xValue, list):
        xResult = [_DoToFloat(x) for x in _xValue]

    else:
        xResult = convert.ToFloat(_xValue)
    # endif

    return xResult


# endif


################################################################################
@tooltip("Convert argument to float")
def ToFloat(_xParser, _lArgs, _lArgIsProc, *, sFuncName):
    if not all(_lArgIsProc):
        return None, False
    # endif

    iArgCnt = len(_lArgs)

    if iArgCnt == 0:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="Expected at least 1 argument but {0} were given".format(iArgCnt),
        )
    # endif

    if iArgCnt == 1:
        xResult = _DoToFloat(_lArgs[0])
    else:
        xResult = _DoToFloat(_lArgs)
    # endif

    return xResult, False


# enddef


################################################################################
@tooltip("Sort list given in first argument, second argument optional for reverse sort")
def Sort(_xParser, _lArgs, _lArgIsProc, *, sFuncName):
    if not all(_lArgIsProc):
        return None, False
    # endif

    iArgCnt = len(_lArgs)

    if iArgCnt < 1 or iArgCnt > 2:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="1 or 2 arguments are expected but {0} were given".format(iArgCnt),
        )
    # endif

    if not isinstance(_lArgs[0], list):
        raise CParserError_FuncMessage(sFunc=sFuncName, sMsg="First argument must be a list")
    # endif

    bReverse = False
    if iArgCnt > 1:
        bReverse = convert.ToBool(_lArgs[1])
    # endif

    try:
        xResult = _lArgs[0].copy()
        xResult.sort(reverse=bReverse)
    except Exception as xEx:
        raise CParserError_FuncMessage(sFunc=sFuncName, sMsg="Error sorting list", xChildEx=xEx)
    # endtry

    return xResult, False


# enddef


################################################################################
@tooltip("Selects a list element based on a modulo circle. Cannot go out of bounds as long as the index is an integer.")
def CircularSelect(_xParser, _lArgs, _lArgIsProc, *, sFuncName):
    if not all(_lArgIsProc):
        return None, False
    # endif

    iArgCnt = len(_lArgs)

    if iArgCnt != 2:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="Expected 2 arguments but {0} were given".format(iArgCnt),
        )
    # endif

    if not isinstance(_lArgs[0], list):
        raise CParserError_FuncMessage(sFunc=sFuncName, sMsg="First argument must be a list")
    # endif

    iArg1 = None
    if isinstance(_lArgs[1], int):
        iArg1 = _lArgs[1]
    elif isinstance(_lArgs[1], str):
        try:
            iArg1 = int(_lArgs[1])
        except Exception as xEx:
            raise CParserError_FuncMessage(
                sFunc=sFuncName,
                sMsg="Error converting second argument to 'int': {}".format(str(xEx)),
            )
        # endtry
    else:
        raise CParserError_FuncMessage(sFunc=sFuncName, sMsg="Second argument must be int or int-convertible string")
    # endif

    xResult = _lArgs[0][iArg1 % len(_lArgs[0])]

    return xResult, False


# enddef


################################################################################
@tooltip("Join strings given as list in the first argument using the string given in the second argument as separator")
def JoinStrings(_xParser, _lArgs, _lArgIsProc, *, sFuncName):
    if not all(_lArgIsProc):
        return None, False
    # endif

    iArgCnt = len(_lArgs)

    if iArgCnt < 1 or iArgCnt > 2:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="The join function must have 1 or 2 arguments but {0} were given".format(iArgCnt),
        )
    # endif

    lData = _lArgs[0]
    if not isinstance(lData, list):
        raise CParserError_FuncMessage(sFunc=sFuncName, sMsg="The first argument has to be a list")
    # endif

    sSep = ""
    if iArgCnt >= 2:
        sSep = _lArgs[1]
        if not isinstance(sSep, str):
            raise CParserError_FuncMessage(sFunc=sFuncName, sMsg="The separator argument has to be a string")
        # endif
    # endif

    xResult = sSep.join(lData)

    return xResult, False


# enddef


################################################################################
@tooltip("If argument 1 is true evaluate argument 2 else argument 3")
def IfCall(_xParser, _lArgs, _lArgIsProc, *, sFuncName):
    iArgCnt = len(_lArgs)

    if iArgCnt < 2 or iArgCnt > 3:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="2 or 3 arguments are expected but {0} were given".format(iArgCnt),
        )
    # endif

    lArgCondition = [_lArgs[0]]
    lArgTrue = [_lArgs[1]]
    if iArgCnt == 3:
        lArgFalse = [_lArgs[2]]
    else:
        lArgFalse = None
    # endif

    # Process first argument, which should be the condition
    try:
        lVarData, lVarIsProc = _xParser._ProcessArgs(lArgCondition)
    except Exception as xEx:
        raise CParserError_ProcFuncArgs(sFunc=sFuncName, lArgs=lArgCondition, xChildEx=xEx)
    # endtry

    if lVarIsProc[0] is False:
        return None, False
    # endif

    try:
        bCondition = convert.ToBool(lVarData[0])
    except Exception as xEx:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="Condition '{}' cannot be converted to bool".format(lVarData[0]),
            xChildEx=xEx,
        )
    # endtry

    if bCondition is True:
        # Process second argument
        try:
            lVarData, lVarIsProc = _xParser._ProcessArgs(lArgTrue)
        except Exception as xEx:
            raise CParserError_ProcFuncArgs(sFunc=sFuncName, lArgs=lArgTrue, xChildEx=xEx)
        # endtry

        if lVarIsProc[0] is False:
            return None, False
        # endif

        xResult = lVarData[0]

    else:
        if lArgFalse is None:
            return None, False
        # endif

        # Process second argument
        try:
            lVarData, lVarIsProc = _xParser._ProcessArgs(lArgFalse)
        except Exception as xEx:
            raise CParserError_ProcFuncArgs(sFunc=sFuncName, lArgs=lArgFalse, xChildEx=xEx)
        # endtry

        if lVarIsProc[0] is False:
            return None, False
        # endif

        xResult = lVarData[0]
    # endif

    return xResult, False


# enddef


################################################################################
@tooltip("Set log path to argument")
def SetLogPath(_xParser, _lArgs, _lArgIsProc, *, sFuncName):
    if not all(_lArgIsProc):
        return None, False
    # endif

    iArgCnt = len(_lArgs)

    if iArgCnt > 1:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="Expected 0 or 1 argument but {0} were given".format(iArgCnt),
        )
    # endif

    if iArgCnt == 0:
        pathLog = _xParser.SetLogFilePath()

    else:
        pathLog = _xParser.SetLogFilePath(_xPath=_lArgs[0], _bCreate=True)
    # endif
    xResult = pathLog.as_posix()

    return xResult, False


# enddef


################################################################################
@tooltip("Print argument to log")
def Print(_xParser, _lArgs, _lArgIsProc, *, sFuncName):
    iArgCnt = len(_lArgs)

    if iArgCnt == 0:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="Expected at least 1 argument but {0} were given".format(iArgCnt),
        )
    # endif

    if iArgCnt == 1:
        sText = str(_lArgs[0])
    else:
        # lText = []
        # for xArg in _lArgs:
        #     if isinstance(xArg, dict) or isinstance(xArg, list):
        #         sText = json.dumps(xArg, indent=4)
        #     else:
        #         sText = str(xArg)
        #     # endif
        #     lText.append(sText)
        # # endfor
        lText = [str(x) for x in _lArgs]
        sText = "\n".join(lText)
    # endif

    _xParser.LogString(sText)

    return None, False
    # return sText, False


# enddef


################################################################################
__ison_functions__ = {
    #####################################################################
    "": {"funcExec": Reference, "bLiteralArgs": True},
    #####################################################################
    # Lambda function related function
    "L": {"funcExec": Lambda, "bLiteralArgs": True},
    "L*": {"funcExec": LambdaDef, "bLiteralArgs": True},
    # '>' only kept for backward compatibility.
    # Is replaced by '!', since '>' is replaced by an escaped unicode
    # control value by pyjson5, so that it can be passed in an URL.
    ">": {"funcExec": LambdaCall, "bLiteralArgs": False},
    "!": {"funcExec": LambdaCall, "bLiteralArgs": False},
    "!foreach": {"funcExec": LambdaCall_ForEach_Arg, "bLiteralArgs": False},
    "!*": {"funcExec": LambdaCall_ForEach_Arg, "bLiteralArgs": False},
    "!where": {"funcExec": LambdaCall_ForEach_Where, "bLiteralArgs": False},
    "!?": {"funcExec": LambdaCall_ForEach_Where, "bLiteralArgs": False},
    #####################################################################
    # Data Structure functions
    "enumerate": {"funcExec": Enumerate, "bLiteralArgs": False},
    "group": {"funcExec": Group, "bLiteralArgs": False},
    "union": {"funcExec": ToUnion, "bLiteralArgs": False},
    "range": {"funcExec": ToRange, "bLiteralArgs": False},
    "sort": {"funcExec": Sort, "bLiteralArgs": False},
    "len": {"funcExec": Len, "bLiteralArgs": False},
    "circularselect": {"funcExec": CircularSelect, "bLiteralArgs": False},
    #####################################################################
    # Logic Functions
    "and": {"funcExec": BoolAnd, "bLiteralArgs": False},
    "eq": {"funcExec": TestEqual, "bLiteralArgs": False},
    "if": {"funcExec": IfCall, "bLiteralArgs": True},
    "or": {"funcExec": BoolOr, "bLiteralArgs": False},
    "not": {"funcExec": BoolNot, "bLiteralArgs": False},
    #####################################################################
    # String
    "join": {"funcExec": JoinStrings, "bLiteralArgs": False},
    "str": {"funcExec": ToString, "bLiteralArgs": False},
    #####################################################################
    # Conversion functions
    "bool": {"funcExec": ToBool, "bLiteralArgs": False},
    "float": {"funcExec": ToFloat, "bLiteralArgs": False},
    "int": {"funcExec": ToInt, "bLiteralArgs": False},
    "json": {"funcExec": ToJson, "bLiteralArgs": False},
    "to-ref-path": {"funcExec": ToRefPath, "bLiteralArgs": False},
    #####################################################################
    # Special functions
    "*": {"funcExec": ToStruct, "bLiteralArgs": False},
    "S": {"funcExec": AsString, "bLiteralArgs": True},
    "Sb": {"funcExec": AsStringBackQuote, "bLiteralArgs": True},
    "print": {"funcExec": Print, "bLiteralArgs": False},
    "set-log-path": {"funcExec": SetLogPath, "bLiteralArgs": False},
}
