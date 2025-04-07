#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \ison\func\file.py
# Created Date: Tuesday, February 15th 2022, 11:57:14 am
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

import math
import copy
import hashlib
import random
import re

# from pathlib import Path
from typing import Tuple

# from ..util import io
from ..util import convert
from ..core import var_nt
from ..core.cls_parser_error import CParserError, CParserError_FuncMessage


def tooltip(sTooltip):
    def inner(func):
        func.tooltip = sTooltip
        return func

    return inner


################################################################################
@tooltip("Calculate sum of all arguments")
def SumValues(_xParser, _lArgs, _lArgIsProc, *, sFuncName):
    if not all(_lArgIsProc):
        return None, False
    # endif

    iArgCnt = len(_lArgs)

    if iArgCnt < 1:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="The add function must have at least 1 argument but {0} were given".format(iArgCnt),
        )
    # endif

    lNewArgs = None
    if any((isinstance(x, float) for x in _lArgs)) or all((isinstance(x, str) for x in _lArgs)):
        try:
            lNewArgs = [float(x) for x in _lArgs]
        except Exception as xEx:
            raise CParserError_FuncMessage(
                sFunc=sFuncName,
                sMsg="Error converting list of summation elements to 'float': {}".format(str(xEx)),
            )
        # endtry

    elif any((isinstance(x, int) for x in _lArgs)):
        try:
            lNewArgs = [int(x) for x in _lArgs]
        except Exception as xEx:
            raise CParserError_FuncMessage(
                sFunc=sFuncName,
                sMsg="Error converting list of summation elements to 'int': {}".format(str(xEx)),
            )
        # endtry

    else:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="Function 'sum': given value types cannot be added: {}".format(_lArgs),
        )
    # endif

    xValue = sum(lNewArgs)

    if isinstance(xValue, float):
        if xValue == math.trunc(xValue):
            xResult = int(xValue)
        else:
            xResult = xValue
        # endif
    else:
        xResult = xValue
    # endif

    return xResult, False


# enddef


################################################################################
@tooltip("Calculate difference between the two arguments")
def SubValues(_xParser, _lArgs, _lArgIsProc, *, sFuncName):
    if not all(_lArgIsProc):
        return None, False
    # endif

    iArgCnt = len(_lArgs)

    if iArgCnt != 2:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="Function 'sub': exactly 2 arguments are expected but {0} were given".format(iArgCnt),
        )
    # endif

    lNewArgs = None
    if any((isinstance(x, float) for x in _lArgs)) or all((isinstance(x, str) for x in _lArgs)):
        try:
            lNewArgs = [float(x) for x in _lArgs]
        except Exception as xEx:
            raise CParserError_FuncMessage(
                sFunc=sFuncName,
                sMsg="Error converting list of subtraction elements to 'float': {}".format(str(xEx)),
            )
        # endtry

    elif any((isinstance(x, int) for x in _lArgs)):
        try:
            lNewArgs = [int(x) for x in _lArgs]
        except Exception as xEx:
            raise CParserError_FuncMessage(
                sFunc=sFuncName,
                sMsg="Error converting list of subtraction elements to 'int': {}".format(str(xEx)),
            )
        # endtry

    else:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="Function 'sum': given value types cannot be added: {}".format(_lArgs),
        )
    # endif

    xValue = lNewArgs[0] - lNewArgs[1]

    if isinstance(xValue, float):
        if xValue == math.trunc(xValue):
            xResult = int(xValue)
        else:
            xResult = xValue
        # endif
    else:
        xResult = xValue
    # endif

    return xResult, False


# enddef


################################################################################
@tooltip("Calculate division of the two arguments")
def DivValues(_xParser, _lArgs, _lArgIsProc, *, sFuncName):
    if not all(_lArgIsProc):
        return None, False
    # endif

    iArgCnt = len(_lArgs)

    if iArgCnt != 2:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="Function 'sub': exactly 2 arguments are expected but {0} were given".format(iArgCnt),
        )
    # endif

    lNewArgs = None
    if any((isinstance(x, float) for x in _lArgs)) or all((isinstance(x, str) for x in _lArgs)):
        try:
            lNewArgs = [float(x) for x in _lArgs]
        except Exception as xEx:
            raise CParserError_FuncMessage(
                sFunc=sFuncName,
                sMsg="Error converting list of subtraction elements to 'float': {}".format(str(xEx)),
            )
        # endtry

    elif any((isinstance(x, int) for x in _lArgs)):
        try:
            lNewArgs = [int(x) for x in _lArgs]
        except Exception as xEx:
            raise CParserError_FuncMessage(
                sFunc=sFuncName,
                sMsg="Error converting list of subtraction elements to 'int': {}".format(str(xEx)),
            )
        # endtry

    else:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="Function 'sum': given value types cannot be added: {}".format(_lArgs),
        )
    # endif

    xValue = lNewArgs[0] / lNewArgs[1]

    if isinstance(xValue, float):
        if xValue == math.trunc(xValue):
            xResult = int(xValue)
        else:
            xResult = xValue
        # endif
    else:
        xResult = xValue
    # endif

    return xResult, False


# enddef


################################################################################
@tooltip("Evalute product of all arguments")
def ProdValues(_xParser, _lArgs, _lArgIsProc, *, sFuncName):
    if not all(_lArgIsProc):
        return None, False
    # endif

    iArgCnt = len(_lArgs)

    if iArgCnt < 1:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="The product function must have at least 1 argument but {0} were given".format(iArgCnt),
        )
    # endif

    # print(f"PRODUCT: lArgs: {_lArgs}")
    bHasFloat = False
    lNewArgs = []
    for xArg in _lArgs:
        if isinstance(xArg, str):
            xNewArg = None
            try:
                xNewArg = int(xArg)
            except Exception:
                pass
            # endtry

            if xNewArg is None:
                try:
                    xNewArg = float(xArg)
                except Exception as xEx:
                    raise CParserError_FuncMessage(
                        sFunc=sFuncName,
                        sMsg="Error converting product element '{}' to int or float: {}".format(xArg, str(xEx)),
                    )
                # endtry
            # endif

        elif isinstance(xArg, int):
            xNewArg = xArg

        elif isinstance(xArg, float):
            if xArg == math.trunc(xArg):
                xNewArg = int(xArg)
            else:
                xNewArg = xArg
            # endif

        else:
            raise CParserError_FuncMessage(sFunc=sFuncName, sMsg="Invalid product element '{}'".format(xArg))
        # endif

        if isinstance(xNewArg, float):
            bHasFloat = True
        # endif

        lNewArgs.append(xNewArg)
    # endfor

    if bHasFloat is True:
        lNewArgs = [float(x) for x in lNewArgs]
    # endif

    # print(f"PRODUCT: lNewArgs: {lNewArgs}")

    xValue = math.prod(lNewArgs)

    # print(f"PRODUCT: xValue: {xValue}")

    if isinstance(xValue, float):
        if xValue == math.trunc(xValue):
            xResult = int(xValue)
        else:
            xResult = xValue
        # endif
    else:
        xResult = xValue
    # endif

    return xResult, False


# enddef


################################################################################
@tooltip("Evalute modulus of first argument with second")
def ModValues(_xParser, _lArgs, _lArgIsProc, *, sFuncName):
    if not all(_lArgIsProc):
        return None, False
    # endif

    iArgCnt = len(_lArgs)

    if iArgCnt != 2:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="Function 'mod': exactly 2 arguments are expected but {0} were given".format(iArgCnt),
        )
    # endif

    lNewArgs = None
    if any((isinstance(x, float) for x in _lArgs)) or all((isinstance(x, str) for x in _lArgs)):
        try:
            lNewArgs = [float(x) for x in _lArgs]
        except Exception as xEx:
            raise CParserError_FuncMessage(
                sFunc=sFuncName,
                sMsg="Error converting modulo arguments to 'float': {}".format(str(xEx)),
            )
        # endtry

    elif any((isinstance(x, int) for x in _lArgs)):
        try:
            lNewArgs = [int(x) for x in _lArgs]
        except Exception as xEx:
            raise CParserError_FuncMessage(
                sFunc=sFuncName,
                sMsg="Error converting modulo arguments to 'int': {}".format(str(xEx)),
            )
        # endtry

    else:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="Function 'mod': modulo cannot be applied to given value types: {}".format(_lArgs),
        )
    # endif

    xValue = lNewArgs[0] % lNewArgs[1]

    if isinstance(xValue, float):
        if xValue == math.trunc(xValue):
            xResult = int(xValue)
        else:
            xResult = xValue
        # endif
    else:
        xResult = xValue
    # endif

    return xResult, False


# enddef


################################################################################
def _ProvideRndGen(_xParser, _iGenId: int, _iSeed: int) -> random.Random:
    dicRndGen = _xParser.dicFuncStorage.get("dicRndGen")
    if dicRndGen is None:
        dicRndGen = _xParser.dicFuncStorage["dicRndGen"] = {}
    # endif

    xGen = dicRndGen.get(_iGenId)
    if xGen is None:
        xGen = random.Random(_iSeed)
        dicRndGen[_iGenId] = xGen
    # endif

    return xGen


# enddef


################################################################################
def _DoRandGenerator(_xParser, _lArgs, *, sFuncName):
    iArgCnt = len(_lArgs)

    if iArgCnt > 1:
        raise CParserError_FuncMessage(sFunc=sFuncName, sMsg=f"Expect 0 or 1 argument but {iArgCnt} were given")
    # endif

    xSeed = None
    if iArgCnt == 1:
        xSeed = _lArgs[0]
        if not isinstance(xSeed, int) and not isinstance(xSeed, float) and not isinstance(xSeed, str):
            raise CParserError_FuncMessage(sFunc=sFuncName, sMsg=f"Seed argument must be int, float or string")
        # endif
    # endif

    if isinstance(xSeed, int):
        iSeed = xSeed
    else:
        sSeed = str(xSeed)
        hashSeed = hashlib.md5(sSeed.encode())
        iSeed = int.from_bytes(hashSeed.digest()[:8], "little")
    # endif

    iGenId = iSeed
    dicRndGen = _xParser.dicFuncStorage.get("dicRndGen")
    if dicRndGen is None:
        dicRndGen = _xParser.dicFuncStorage["dicRndGen"] = {}
    # endif

    while iGenId in dicRndGen:
        iGenId += 1
    # endwhile

    xGen = random.Random(iSeed)
    dicRndGen[iGenId] = xGen

    return f":eval:rand.generator({iGenId}):[{iSeed}]"


# enddef


################################################################################
def _GetRndGenDefault(_xParser) -> random.Random:
    return _ProvideRndGen(_xParser, 0, 0)


# enddef


################################################################################
def _GetRndGenFromEvalId(_xParser, _sGenEval: str) -> random.Random:
    xMatch = re.match(r":eval:rand.generator\((?P<genid>[-\d]+)\):\[(?P<seed>[-\w]+)\]", _sGenEval)
    if xMatch is None:
        return None
    # endif

    # ### DEBUG ###
    # sId = xMatch.group("genid")
    # sSeed = xMatch.group("seed")
    # print(f"Using random generator id[{sId}], seed[{sSeed}]")
    # #############

    iGenId = int(xMatch.group("genid"))
    iSeed = int(xMatch.group("seed"))
    xGen = _ProvideRndGen(_xParser, iGenId, iSeed)

    return xGen


# enddef


################################################################################
def _GetRndGenFromArgs(_xParser, _lArgs: list) -> Tuple[random.Random, list]:
    if len(_lArgs) == 0:
        xGen = _GetRndGenDefault(_xParser)
        return xGen, _lArgs
    # endif

    if isinstance(_lArgs[0], str):
        xGen = _GetRndGenFromEvalId(_xParser, _lArgs[0])
        if xGen is None:
            xGen = _GetRndGenDefault(_xParser)
            return xGen, _lArgs
        # endif

        return xGen, _lArgs[1:]
    # endif

    xGen = _GetRndGenDefault(_xParser)
    return xGen, _lArgs


# enddef


################################################################################
def _DoRandSeed(_xParser, _lArgs, *, sFuncName):
    iArgCnt = len(_lArgs)

    if iArgCnt > 2:
        raise CParserError_FuncMessage(sFunc=sFuncName, sMsg=f"Expect 0, 1 or 2 arguments but {iArgCnt} were given")
    # endif

    xGen, lArgs = _GetRndGenFromArgs(_xParser, _lArgs)
    iArgCnt = len(lArgs)

    xSeed = None
    if iArgCnt == 1:
        xSeed = lArgs[0]
        if not isinstance(xSeed, int) and not isinstance(xSeed, float) and not isinstance(xSeed, str):
            raise CParserError_FuncMessage(sFunc=sFuncName, sMsg="Seed argument must be int, float or string")
        # endif
    # endif

    xGen.seed(xSeed)
    # Keep this for backward compatibility
    random.seed(xSeed)

    return f":eval:{sFuncName}:{_lArgs}"


# enddef


################################################################################
def _DoRandUniform(_xParser, _lArgs, *, sFuncName):
    xResult = None

    iArgCnt = len(_lArgs)

    if iArgCnt < 2 or iArgCnt > 3:
        raise CParserError_FuncMessage(sFunc=sFuncName, sMsg=f"Expect 2 or 3 arguments but {iArgCnt} were given")
    # endif

    xGen, lArgs = _GetRndGenFromArgs(_xParser, _lArgs)
    iArgCnt = len(lArgs)

    try:
        fMin = convert.ToFloat(lArgs[0])
        fMax = convert.ToFloat(lArgs[1])

    except Exception as xEx:
        raise CParserError_FuncMessage(sFunc=sFuncName, sMsg=f"Invalid argument", xChildEx=xEx)
    # endtry

    xResult = xGen.uniform(fMin, fMax)

    return xResult


# enddef


################################################################################
def _DoRandUniformInt(_xParser, _lArgs, *, sFuncName):
    xResult = None

    iArgCnt = len(_lArgs)

    if iArgCnt < 2 or iArgCnt > 3:
        raise CParserError_FuncMessage(sFunc=sFuncName, sMsg=f"Expect 2 or 3 arguments but {iArgCnt} were given")
    # endif

    xGen, lArgs = _GetRndGenFromArgs(_xParser, _lArgs)
    iArgCnt = len(lArgs)

    try:
        iMin = convert.ToInt(lArgs[0])
        iMax = convert.ToInt(lArgs[1])

    except Exception as xEx:
        raise CParserError_FuncMessage(sFunc=sFuncName, sMsg=f"Invalid argument", xChildEx=xEx)
    # endtry

    xResult = xGen.randint(iMin, iMax)

    return xResult


# enddef


################################################################################
def _RandomSelectInDict(_dicVal: dict, _xGen: random.Random):
    dicSel = {}
    for sKey in _dicVal:
        xValue = _dicVal[sKey]
        if isinstance(xValue, list):
            dicSel[sKey] = _xGen.choice(xValue)

        elif isinstance(xValue, dict):
            dicSel[sKey] = _RandomSelectInDict(xValue, _xGen)

        else:
            dicSel[sKey] = xValue

        # endif
    # endfor

    return dicSel


# enddef


################################################################################
def _DoRandZwicky(_xParser, _lArgs, *, sFuncName):
    iArgCnt = len(_lArgs)

    if iArgCnt < 1 or iArgCnt > 2:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="Function {0} expects at 1 or 2 arguments but {1} were given".format(sFuncName, iArgCnt),
        )
    # endif

    xGen, lArgs = _GetRndGenFromArgs(_xParser, _lArgs)
    iArgCnt = len(lArgs)

    dicVal = lArgs[0]
    if not isinstance(dicVal, dict):
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="The argument of function '{0}' is not a dictionary".format(sFuncName),
        )
    # endif

    dicProc, bIsProc = _xParser.InnerProcess(dicVal)
    xResult = _RandomSelectInDict(dicProc, xGen)

    return xResult


# enddef


################################################################################
def _DoRandChoice(_xParser, _lArgs, *, sFuncName):
    iArgCnt = len(_lArgs)

    if iArgCnt < 1 or iArgCnt > 2:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="Function {0} expects 1 or 2 arguments but {1} were given".format(sFuncName, iArgCnt),
        )
    # endif

    xGen, lArgs = _GetRndGenFromArgs(_xParser, _lArgs)

    xVal = lArgs[0]

    # dicProc, bIsProc = _xParser.InnerProcess(xVal)
    if isinstance(xVal, list):
        xResult = xGen.choice(xVal)

    elif isinstance(xVal, dict):
        sKey = xGen.choice(list(xVal.keys()))
        xResult = xVal[sKey]

    else:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="The argument of function '{0}' is not a dictionary".format(sFuncName),
        )
    # endif

    return xResult


# enddef


################################################################################
def _DoRandSample(_xParser, _lArgs, *, sFuncName):
    iArgCnt = len(_lArgs)

    if iArgCnt < 2 or iArgCnt > 4:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="Function {0} expects 2, 3 or 4 arguments but {1} were given".format(sFuncName, iArgCnt),
        )
    # endif

    xGen, lArgs = _GetRndGenFromArgs(_xParser, _lArgs)

    iArgCnt = len(lArgs)
    xData = lArgs[0]

    try:
        iSampleCnt = convert.ToInt(lArgs[1])

    except Exception as xEx:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="The sample count must be an integer, not: {}".format(lArgs[1]),
            xChildEx=xEx,
        )
    # endtry

    bUnique = True
    if iArgCnt >= 3:
        try:
            bUnique = convert.ToBool(lArgs[2])
        except Exception as xEx:
            raise CParserError_FuncMessage(
                sFunc=sFuncName,
                sMsg="The third parameter must be convertible to boolean, "
                "to indicate whether the sampled elements are unique (true, default) "
                "or not (false)",
                xChildEx=xEx,
            )
        # endtry
    # endif

    # dicProc, bIsProc = _xParser.InnerProcess(xVal)

    if isinstance(xData, list):
        if bUnique is True:
            if len(xData) < iSampleCnt:
                raise CParserError_FuncMessage(sFunc=sFuncName, sMsg="The sample count is larger than the sample pool")
            # endif
            xResult = xGen.sample(xData, iSampleCnt)

        else:
            lIdx = [xGen.randrange(len(xData)) for i in range(iSampleCnt)]
            xResult = [xData[iIdx] for iIdx in lIdx]
        # endif

    elif isinstance(xData, dict):
        lData = list(xData.keys())

        if bUnique is True:
            if len(lData) < iSampleCnt:
                raise CParserError_FuncMessage(sFunc=sFuncName, sMsg="The sample count is larger than the sample pool")
            # endif
            lSample = xGen.sample(lData, iSampleCnt)

        else:
            lIdx = [xGen.randrange(len(lData)) for i in range(iSampleCnt)]
            lSample = [lData[iIdx] for iIdx in lIdx]
        # endif

        xResult = {}
        for sKey in lSample:
            xResult[sKey] = copy.deepcopy(xData[sKey])
        # endfor

    else:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="The argument of function '{0}' is not a dictionary".format(sFuncName),
        )
    # endif

    return xResult


# enddef


################################################################################
def _DoRandSampleRange(_xParser, _lArgs, *, sFuncName):
    iArgCnt = len(_lArgs)

    if iArgCnt < 3 or iArgCnt > 6:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg=f"Function {sFuncName} expects 3 to 6 arguments but {iArgCnt} were given",
        )
    # endif

    xGen, lArgs = _GetRndGenFromArgs(_xParser, _lArgs)
    iArgCnt = len(lArgs)

    try:
        iMin: int = convert.ToInt(lArgs[0])

    except Exception as xEx:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="The minimum value must be an integer, not: {}".format(lArgs[0]),
            xChildEx=xEx,
        )
    # endtry

    try:
        iMax: int = convert.ToInt(lArgs[1])

    except Exception as xEx:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="The maximum value must be an integer, not: {}".format(lArgs[1]),
            xChildEx=xEx,
        )
    # endtry

    try:
        iSampleCnt: int = convert.ToInt(lArgs[2])

    except Exception as xEx:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="The sample count must be an integer, not: {}".format(lArgs[2]),
            xChildEx=xEx,
        )
    # endtry

    bUnique = True
    bConsecDiffer = False
    if iArgCnt >= 4:
        try:
            for tArg in lArgs[3:]:
                dicData = var_nt.GetData(tArg)
                if dicData is None:
                    raise CParserError_FuncMessage(
                        sFunc=sFuncName,
                        sMsg="Malformed optional argument: {}".format(tArg),
                    )
                # endif

                for sKey in dicData:
                    sValue = dicData[sKey]

                    if sKey == "unique":
                        bUnique = convert.ToBool(sValue)

                    elif sKey == "consec-differ":
                        bConsecDiffer = convert.ToBool(sValue)

                    else:
                        raise CParserError_FuncMessage(
                            sFunc=sFuncName,
                            sMsg="Unsupported optional argrument: {}".format(sValue),
                        )
                    # endif
                # endfor
            # endfor
        except Exception as xEx:
            raise CParserError_FuncMessage(sFunc=sFuncName, sMsg="Error parsing optional arguments", xChildEx=xEx)
        # endtry
    # endif

    if iMax < iMin:
        iX = iMin
        iMin = iMax
        iMax = iX
    # endif

    if iSampleCnt <= 0:
        raise CParserError_FuncMessage(
            sFunc=sFuncName, sMsg=f"Sample count must be greater than zero but is {iSampleCnt}"
        )
    # endif

    iRange: int = iMax - iMin + 1
    if bUnique is True and iSampleCnt > iRange:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg=(
                f"The sample count ({iSampleCnt}) is larger than "
                f"the range ({iRange}) but unique sampling is enabled"
            ),
        )
    # endif

    lValues: list[int] = []
    if bUnique is True:
        setValues: set[int] = set()
        while True:
            iRndVal = xGen.randint(iMin, iMax)
            if iRndVal in setValues:
                continue
            # endif
            setValues.add(iRndVal)

            if len(setValues) >= iSampleCnt:
                break
            # endif
        # endfor
        lValues = list(setValues)

    elif bConsecDiffer is True:
        iRndVal = xGen.randint(iMin, iMax)
        iPrevVal = iRndVal
        lValues = [iRndVal]
        while True:
            if len(lValues) >= iSampleCnt:
                break
            # endif

            iRndVal = xGen.randint(iMin, iMax)
            if iRndVal == iPrevVal:
                continue
            # endif
            lValues.append(iRndVal)
            iPrevVal = iRndVal
        # endfor

    else:
        lValues = [xGen.randint(iMin, iMax) for i in range(iSampleCnt)]
    # endif

    return lValues


# enddef


################################################################################
@tooltip("Various random functions: rand.seed, .uniform, .int, .zwicky, .choice, .sample, .sample_range")
def RandomFuncGrp(
    _xParser,
    _lArgs: list,
    _lArgIsProc: list[bool],
    *,
    sFuncName: str,
    lFuncParts: list[str],
):
    if not all(_lArgIsProc):
        return None, False
    # endif

    sSubFunc: str = ".".join(lFuncParts[1:])

    dicSubFuncs = {
        "generator": _DoRandGenerator,
        "seed": _DoRandSeed,
        "uniform": _DoRandUniform,
        "int": _DoRandUniformInt,
        "zwicky": _DoRandZwicky,
        "choice": _DoRandChoice,
        "sample": _DoRandSample,
        "sample_range": _DoRandSampleRange,
    }

    if sSubFunc not in dicSubFuncs:
        raise CParserError_FuncMessage(sFunc=sFuncName, sMsg=f"Function {sFuncName} not defined")
    # endif

    xResult = dicSubFuncs[sSubFunc](_xParser, _lArgs, sFuncName=sFuncName)

    return xResult, False


# enddef


################################################################################
__ison_functions__ = {
    "sum": {"funcExec": SumValues, "bLiteralArgs": False},
    "sub": {"funcExec": SubValues, "bLiteralArgs": False},
    "div": {"funcExec": DivValues, "bLiteralArgs": False},
    "prod": {"funcExec": ProdValues, "bLiteralArgs": False},
    "mod": {"funcExec": ModValues, "bLiteralArgs": False},
    "rand.*": {"funcExec": RandomFuncGrp, "bLiteralArgs": False},
}
