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
import re
from typing import Union
from ..util import text
from ..core import var_nt

from .defines import (
    reLambdaFunc,
    reEscString,
    reString,
    reLambdaPar,
    reNamedArg,
    reVarStart,
)


from .cls_parser_error import (
    CParserError_Message,
    CParserError_ProcLambdaArgs,
    CParserError_ProcStr,
    CParserError_ProcLambdaPart,
)


################################################################################
def FindLambdaScope(_sBody):

    lScope = []

    iStart = 0
    while True:
        xMatch = reLambdaFunc.search(_sBody, iStart)
        if xMatch is not None:
            lScope.append([iStart, xMatch.start()])

            iArgStartIdx = xMatch.end()
            iStart = 1 + text.FindBalancedChar(_sBody, iArgStartIdx - 1, "}")
        else:
            lScope.append([iStart, len(_sBody)])
            break
        # endif
    # endwhile

    return lScope


# enddef


################################################################################
def NormLambdaIndices(_sBody: str, _lScope: list[list[int]]) -> Union[str, bool]:

    bHasPars: bool = False
    lIndices: list = []
    setIndices: set = set()

    # sB: str = ""
    # iPartEnd: int = 0
    for lPart in _lScope:
        bPartHasIdxPars: bool = False
        bPartHasNamedArgs: bool = False

        # sB += _sBody[iPartEnd:lPart[0]]
        sBodyPart = _sBody[lPart[0] : lPart[1]]
        # iPartEnd = lPart[1]

        iStart = 0
        while True:
            xMatch = reLambdaPar.search(sBodyPart, max(iStart - 1, 0))
            if xMatch is None:
                break
            # endif
            sIdxGrpName: str = None

            if xMatch.group("idx") is not None:
                sIdxGrpName = "idx"
            elif xMatch.group("name_idx") is not None:
                sIdxGrpName = "name_idx"
            else:
                bPartHasNamedArgs = True
            # endif

            if sIdxGrpName is not None:
                iIdx = int(xMatch.group(sIdxGrpName))
                lIndices.append(
                    (
                        iIdx,
                        xMatch.start(sIdxGrpName) + lPart[0],
                        xMatch.end(sIdxGrpName) + lPart[0],
                    )
                )
                setIndices.add(iIdx)
            # endif
            iStart = xMatch.end()
        # endfor
        # sB += sBodyPart

    # endfor scope
    # sB += _sBody[iPartEnd:]

    lIdxSet = list(setIndices)

    bPartHasIdxPars = len(lIdxSet) > 0
    bHasPars = bHasPars or bPartHasIdxPars or bPartHasNamedArgs
    if bPartHasIdxPars is False:
        sB = _sBody

    else:
        sB: str = ""
        iStart = 0
        for iIdx, iIdxStart, iIdxEnd in lIndices:
            iNewIdx = lIdxSet.index(iIdx)
            sB += _sBody[iStart:iIdxStart]
            sB += str(iNewIdx)
            iStart = iIdxEnd
        # endfor
        sB += _sBody[iStart:]
    # endif has idx pars

    return sB, bHasPars


# enddef


################################################################################
def ConvertJsonToLambdaStrings(_sText):

    sNewText = re.sub(reEscString, r"$S{\1}", _sText)
    sNewText = re.sub(reString, r"$S{\1}", sNewText)
    return sNewText


# enddef


################################################################################
def ConvertLambdaToJsonStrings(_sText, *, _bInStringContext=False):

    iQuoteCount = 0
    iEnd = 0
    sNewText = ""
    try:
        lMatch = text.GetVarMatchList(_sText, reVarStart, lSingleArgsFuncs="S")
    except Exception as xEx:
        raise CParserError_ProcStr(sString=_sText, sContext="Converting lambda string to object", xChildEx=xEx)
    # endtry

    for dicMatch in lMatch:
        if dicMatch["sFunc"] == "S":
            # if the $S{} block is inside a string ("[...]"),
            # the quotes need to be escaped here.
            iQuoteCount += _sText.count('"', iEnd, dicMatch["iStart"])
            bInString = (iQuoteCount % 2) != 0
            sArg = dicMatch["lArgs"][0]
            sEl: str = None
            if bInString and _bInStringContext:
                # Keep $S{} as is
                sEl = f"$S{{{sArg}}}"

            elif bInString or _bInStringContext:
                sEl = f'\\"{sArg}\\"'

            else:
                # Recurse only one level down for $S{}.
                # That is, $S{Hello $S{World $S{today}}} -> "Hello \"World $S{today}\""
                sProcArg = ConvertLambdaToJsonStrings(sArg, _bInStringContext=True)
                sEl = f'"{sProcArg}"'

            # endif

            sNewText += _sText[iEnd : dicMatch["iStart"]]
            sNewText += sEl
            iEnd = dicMatch["iEnd"]
        # endif
    # endfor
    sNewText += _sText[iEnd:]

    return sNewText


# enddef


################################################################################
def ToLambdaString(_xLambda):

    sLambda = json.dumps(_xLambda)
    sLambda = ConvertJsonToLambdaStrings(sLambda)

    return sLambda


# enddef


################################################################################
def ToLambdaObject(_sLambda):

    sLambda = ConvertLambdaToJsonStrings(_sLambda)
    xLambda = json.loads(sLambda)

    return xLambda


# enddef


################################################################################
# those lambda function arguments that are no strings,
# are converted into a string, wrapped in the unwrap function $*{}.
# The string is passed as literal element to the function via '^',
# so that the string is first converted to a struct and then parsed
# for further replacements.
# Due to the replacement in Lambda functions, there may be mulitply nested strings.
# To handle this, the lambda parser packs strings in arguments into function blocks $S{}.
def ToLambdaArgs(_lArgs):

    lArgs = []
    for xArg in _lArgs:
        if isinstance(xArg, str):
            sNewArg = ConvertJsonToLambdaStrings(xArg)
            lArgs.append(sNewArg)
        elif var_nt.IsValid(xArg):
            xNewArg = var_nt.Empty()
            dicData = var_nt.GetData(xArg)
            for sKey in dicData:
                xNewArg = var_nt.Add(xNewArg, sKey, ToLambdaArgs([dicData[sKey]])[0])
            # endfor
            lArgs.append(xNewArg)
        else:
            sNewArg = ToLambdaString(xArg)
            lArgs.append("$*{{^{0}}}".format(sNewArg))
        # endif
    # endfor

    return lArgs


# enddef


################################################################################
def Parse(_xBody, _lArgs, funcProcess=None):

    if isinstance(_lArgs, list):
        lInArgs = _lArgs
    elif isinstance(_lArgs, tuple):
        lInArgs = list(_lArgs)
    else:
        lInArgs = [_lArgs]
    # endif

    iPosArgCnt = len(lInArgs)
    if iPosArgCnt == 0:
        return _xBody
    # endif

    if funcProcess is not None:
        xResult = funcProcess(_xBody)
    else:
        xResult = _xBody
    # endif

    # sCallBody = json.dumps({"xBody": xResult})
    sCallBody = ToLambdaString(xResult)
    setUsedArgIdx: set = set()
    setUsedArgName: set = set()

    # those lambda function arguments that are no strings,
    # are converted into a string, wrapped in the unwrap function $*{}.
    # The string is passed as literal element to the function via '^',
    # so that the string is first converted to a struct and then parsed
    # for further replacements.
    # Due to the replacement in Lambda functions, there may be mulitply nested strings.
    # To handle this, the lambda parser packs strings in arguments into function blocks $S{}.
    lArgs: list[str] = ToLambdaArgs(lInArgs)
    lPosArgs: str = []
    dicNamedArgs: dict[str, str] = {}

    for xArg in lArgs:
        dicNtArg = var_nt.GetData(xArg)
        if dicNtArg is not None:
            for sKey in dicNtArg:
                if sKey in dicNamedArgs:
                    raise CParserError_Message(sMsg=f"Lambda argument '{sKey}' defined multiple times")
                # endif
                dicNamedArgs[sKey] = text.StripLiteralString(dicNtArg[sKey])
            # endfor
        else:
            xArg = text.StripLiteralString(xArg)
            lPosArgs.append(xArg)
            # endif
        # endif
    # endfor

    # Iterate until all parameters have been processed,
    # or no more lambda functions are in the body.
    bBodyChanged = True

    while True:
        sCB = ""
        iCBStart = 0

        lPosArgs = [x for i, x in enumerate(lPosArgs) if i not in setUsedArgIdx]
        for sArgName in setUsedArgName:
            del dicNamedArgs[sArgName]
        # endfor

        setUsedArgIdx = set()
        setUsedArgName = set()
        iPosArgCnt = len(lPosArgs)
        iNamedArgCnt = len(dicNamedArgs)

        bHasArgs = (iNamedArgCnt + iPosArgCnt) > 0
        bHasLambda = reLambdaFunc.search(sCallBody) is not None

        if bHasArgs is False or bHasLambda is False or bBodyChanged is False:
            break
        # endif

        bBodyChanged = False

        # Loop over all top level Lambda functions in body
        while True:
            xLM = reLambdaFunc.search(sCallBody, iCBStart)
            if xLM is None:
                break
            # endif

            sCB += sCallBody[iCBStart : xLM.start()]

            iBodyStart = xLM.end()

            iBodyEnd = text.FindBalancedChar(sCallBody, iBodyStart - 1, "}")
            iCBStart = iBodyEnd + 1
            sBody = sCallBody[iBodyStart:iBodyEnd]

            lScope = FindLambdaScope(sBody)
            sBody, bHasPars = NormLambdaIndices(sBody, lScope)

            if bHasPars:
                sB = ""
                iPartEnd = 0
                for lPart in lScope:
                    sB += sBody[iPartEnd : lPart[0]]
                    sBodyPart = sBody[lPart[0] : lPart[1]]
                    iPartEnd = lPart[1]

                    iStart = 0
                    while True:
                        xMatch = reLambdaPar.search(sBodyPart, iStart)  # max(iStart-1, 0))
                        if xMatch is None:
                            break
                        # endif
                        # iIdx = int(xMatch.group("idx"))
                        iIdx: int = None
                        sArgKey: str = None
                        if xMatch.group("idx") is not None:
                            iIdx = int(xMatch.group("idx"))
                        elif xMatch.group("name_idx") is not None:
                            iIdx = int(xMatch.group("name_idx"))
                        # endif

                        # sArgKey is only not None, if the var has a name
                        sArgKey = xMatch.group("name")

                        bIsNull = len(xMatch.group("isnull")) > 0
                        if iIdx is not None and iIdx < iPosArgCnt:
                            setUsedArgIdx.add(iIdx)
                            sB += sBodyPart[iStart : xMatch.start()]
                            if not bIsNull:
                                sB += lPosArgs[iIdx]
                                bBodyChanged = True
                            # endif
                        elif sArgKey is not None and sArgKey in dicNamedArgs:
                            setUsedArgName.add(sArgKey)
                            sB += sBodyPart[iStart : xMatch.start()]
                            if not bIsNull:
                                sB += dicNamedArgs[sArgKey]
                                bBodyChanged = True
                            # endif
                        # elif sArgKey is not None and len(dicNamedArgs) == 0:
                        #     raise CParserError_Message(sMsg=f"Named argument '{sArgKey}' not found in lambda function")

                        else:
                            sB += sBodyPart[iStart : xMatch.end()]
                        # endif
                        iStart = xMatch.end()
                    # endwhile body part
                    sB += sBodyPart[iStart:]
                # endfor scope
                sB += sBody[iPartEnd:]

                lScope = FindLambdaScope(sB)
                sB, bHasPars = NormLambdaIndices(sB, lScope)

            else:
                sB = sBody
            # endif bHasPars

            # If the lambda function has no more free parameters,
            # then unwrap it, otherwise re-package the body in $L{}
            if bHasPars:
                sB = "$L{{{0}}}".format(sB)
            # endif

            sCB += sB
        # endwhile lambda function bodies
        sCB += sCallBody[iCBStart:]

        xBody = ToLambdaObject(sCB)

        if funcProcess is not None:
            try:
                xResult = funcProcess(xBody)
            except Exception as xEx:
                raise CParserError_ProcLambdaPart(sPart=sCB, xChildEx=xEx)
            # endtry
        else:
            xResult = xBody
        # endif

        # sCallBody = json.dumps({"xBody": xResult})
        sCallBody = ToLambdaString(xResult)
    # endwhile all parameters have been consumed

    xBody = ToLambdaObject(sCallBody)
    return xBody


# enddef
