#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \cml\cls_parser_exception.py
# Created Date: Sunday, February 13th 2022, 11:46:03 am
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


from typing import Optional
from .cls_parser_trace import CWarningList


class CParserError(RuntimeError):
    def __init__(
        self, *, sMsg, sType=None, xData=None, xSelect=None, xChildEx=None, xWarnings: Optional[CWarningList] = None
    ):

        self.sType = sType
        self.xData = xData
        self.xSelect = xSelect
        self.xChildEx = xChildEx
        self.xWarnings: CWarningList = None

        self.message = sMsg

        super().__init__(self.message)

    # enddef

    ################################################################################
    def __str__(self):
        return self.ToString()

    # enddef

    ################################################################################
    def ToString(self, iLevel=1):

        sMsg = self.IndentLevel(self.message, iLevel)

        if self.xChildEx is not None:
            if isinstance(self.xChildEx, CParserError) is True:
                sMsg += self.xChildEx.ToString(iLevel=iLevel + 1)
            else:
                sMsg += self.IndentLevel(str(self.xChildEx), iLevel + 1)
            # endif
        # endif

        if isinstance(self.xWarnings, CWarningList) and self.xWarnings.bHasWarnings:
            sMsg += "\nAlso consider these WARNING(s):\n" + str(self.xWarnings)
        # endif

        return sMsg

    # enddef

    ################################################################################
    def IndentLevel(self, _sMsg, _iLevel):

        lLines = _sMsg.split("\n")
        sTag1 = f"{_iLevel:2d}> "
        sTagX = "  | "
        sMsg = sTag1 + lLines[0] + "\n"

        for sLine in lLines[1:]:
            sMsg += sTagX + sLine + "\n"
        # endfor

        return sMsg

    # enddef

    ################################################################################
    @staticmethod
    def ListToString(_lArgs, iHighlightIdx=None):

        sMsg = ""
        if _lArgs is None:
            sMsg += "\nNone"
        elif len(_lArgs) == 0:
            sMsg += "\n[]"
        else:
            for iIdx, xArg in enumerate(_lArgs):
                if iHighlightIdx is not None and iHighlightIdx == iIdx:
                    sMsg += "\n>"
                else:
                    sMsg += "\n "
                # endif
                sMsg += "{:2d}: {}".format(iIdx, str(xArg))
            # endfor
        # endif
        return sMsg

    # enddef

    ################################################################################
    @staticmethod
    def ToTypename(xValue):

        if xValue is None:
            return "None"
        # endif

        sType = "unknown"
        if isinstance(xValue, dict):
            sType = "dictionary"

        elif isinstance(xValue, list):
            sType = "list"

        elif isinstance(xValue, tuple):
            sType = "tuple"

        elif isinstance(xValue, str):
            sType = "string"

        elif isinstance(xValue, int):
            sType = "integer"

        elif isinstance(xValue, float):
            sType = "float"

        elif isinstance(xValue, bool):
            sType = "boolean"

        else:
            sType = str(type(xValue))
        # endif

        return sType

    # enddef


# endclass


###########################################################################################
class CParserError_Message(CParserError):
    def __init__(self, *, sMsg, xChildEx=None):

        super().__init__(sMsg=sMsg, sType="message", xData=sMsg, xChildEx=xChildEx)

    # enddef


# endclass


############################################################################################
class CParserError_FuncMessage(CParserError):
    def __init__(self, *, sFunc, sMsg, xChildEx=None):

        sMessage = f"Function '${sFunc}{{}}': {sMsg}"
        super().__init__(
            sMsg=sMessage,
            sType="func-message",
            xData=sFunc,
            xSelect=sMsg,
            xChildEx=xChildEx,
        )

    # enddef


# endclass


###########################################################################################
class CParserError_DictSel(CParserError):
    def __init__(self, *, dicData, xId, xChildEx=None):

        sMsg = "Dictionary element '{}' -> {}".format(str(xId), CParserError.ToTypename(dicData.get(xId)))

        super().__init__(sMsg=sMsg, sType="dict-sel", xData=dicData, xSelect=xId, xChildEx=xChildEx)

    # enddef


# endclass


###########################################################################################
class CParserError_ListSel(CParserError):
    def __init__(self, *, lData, iIdx, sContext=None, xChildEx=None):

        if sContext is None:
            sCtx = "List index"
        else:
            sCtx = sContext
        # endif

        sMsg = "{} {} -> {}".format(sCtx, str(iIdx), CParserError.ToTypename(lData[iIdx]))

        super().__init__(sMsg=sMsg, sType="list-sel", xData=lData, xSelect=iIdx, xChildEx=xChildEx)

    # enddef


# endclass


###########################################################################################
class CParserError_StrMatch(CParserError):
    def __init__(self, *, sString, dicMatch, xChildEx=None):

        iStart = dicMatch["iStart"]
        iEnd = dicMatch["iEnd"]

        sStr = sString[0:iStart]
        sStr += ">>" + sString[iStart:iEnd] + "<<"
        sStr += sString[iEnd:]
        sMsg = "String element: {}".format(sStr)

        super().__init__(
            sMsg=sMsg,
            sType="str-match",
            xData=sString,
            xSelect=dicMatch,
            xChildEx=xChildEx,
        )

    # enddef


# endclass


###########################################################################################
class CParserError_KeyStrMatch(CParserError):
    def __init__(self, *, sString, dicMatch, xChildEx=None):

        iStart = dicMatch["iStart"]
        iEnd = dicMatch["iEnd"]

        sStr = sString[0:iStart]
        sStr += ">>" + sString[iStart:iEnd] + "<<"
        sStr += sString[iEnd:]
        sMsg = "Key string element: {}".format(sStr)

        super().__init__(
            sMsg=sMsg,
            sType="key-str-match",
            xData=sString,
            xSelect=dicMatch,
            xChildEx=xChildEx,
        )

    # enddef


# endclass


###########################################################################################
class CParserError_ProcStr(CParserError):
    def __init__(self, *, sString, sContext=None, xChildEx=None):

        if sContext is None:
            sCtx = "String"
        else:
            sCtx = sContext
        # endif

        sMsg = "{}: {}".format(sCtx, sString)

        super().__init__(sMsg=sMsg, sType="proc-str", xData=sString, xSelect=sCtx, xChildEx=xChildEx)

    # enddef


# endclass

###########################################################################################
class CParserError_ProcKey(CParserError):
    def __init__(self, *, sKey, xChildEx=None):

        sMsg = "Key: {}".format(sKey)

        super().__init__(sMsg=sMsg, sType="proc-key", xData=sKey, xSelect=None, xChildEx=xChildEx)

    # enddef


# endclass


###########################################################################################
class CParserError_ProcArgStr(CParserError):
    def __init__(self, *, sString, sContext=None, xChildEx=None):

        if sContext is None:
            sCtx = "Argument string"
        else:
            sCtx = sContext
        # endif

        sMsg = "{}: {}".format(sCtx, sString)

        super().__init__(
            sMsg=sMsg,
            sType="proc-arg-str",
            xData=sString,
            xSelect=None,
            xChildEx=xChildEx,
        )

    # enddef


# endclass


###########################################################################################
class CParserError_ProcArgListElement(CParserError):
    def __init__(self, *, lArgList, iArgIdx, sContext=None, xChildEx=None):

        if sContext is None:
            sCtx = f"Argument {iArgIdx} of"
        else:
            sCtx = sContext
        # endif

        sMsg = "{}:{}".format(sCtx, CParserError.ListToString(lArgList, iHighlightIdx=iArgIdx))

        super().__init__(
            sMsg=sMsg,
            sType="proc-arg-list-el",
            xData=lArgList,
            xSelect=iArgIdx,
            xChildEx=xChildEx,
        )

    # enddef


# endclass


###########################################################################################
class CParserError_ProcFuncArgs(CParserError):
    def __init__(self, *, sFunc, lArgs, xChildEx=None):

        sMsg = "Arguments for function '${}{{}}':".format(sFunc)
        sMsg += CParserError.ListToString(lArgs)
        super().__init__(
            sMsg=sMsg,
            sType="proc-func-args",
            xData=sFunc,
            xSelect=lArgs,
            xChildEx=xChildEx,
        )

    # enddef


# endclass


###########################################################################################
class CParserError_ProcRefPath(CParserError):
    def __init__(self, *, lMatch, iMatchIdx, sContext, xChildEx=None):

        sMsg = "Referencing {} with:{}".format(sContext, CParserError.ListToString(lMatch, iHighlightIdx=iMatchIdx))

        super().__init__(
            sMsg=sMsg,
            sType="proc-ref-path",
            xData=lMatch,
            xSelect=iMatchIdx,
            xChildEx=xChildEx,
        )

    # enddef


# endclass


###########################################################################################
class CParserError_ProcFunc(CParserError):
    def __init__(self, *, sFunc, lArgs, xChildEx=None):

        sMsg = "Function '${}{{}}' with {} argument(s):".format(sFunc, len(lArgs))
        sMsg += CParserError.ListToString(lArgs)

        super().__init__(sMsg=sMsg, sType="proc-func", xData=sFunc, xSelect=lArgs, xChildEx=xChildEx)

    # enddef


# endclass


###########################################################################################
class CParserError_ProcLambda(CParserError):
    def __init__(self, *, xLambda, lArgs, xChildEx=None):

        sMsg = "Composing lambda:\n" "\t{}\n" ">>\twith arguments:\n" ">>\t{}".format(str(xLambda), str(lArgs))

        super().__init__(
            sMsg=sMsg,
            sType="proc-lambda",
            xData=xLambda,
            xSelect=lArgs,
            xChildEx=xChildEx,
        )

    # enddef


# endclass


###########################################################################################
class CParserError_ProcLambdaArgs(CParserError):
    def __init__(self, *, xLambda, lArgs, xChildEx=None):

        sMsg = "Lambda arguments '{}': {}".format(str(xLambda), str(lArgs))

        super().__init__(
            sMsg=sMsg,
            sType="proc-lambda-args",
            xData=xLambda,
            xSelect=lArgs,
            xChildEx=xChildEx,
        )

    # enddef


# endclass


###########################################################################################
class CParserError_ProcLambdaPart(CParserError):
    def __init__(self, *, sPart, xChildEx=None):

        sMsg = "Lambda part: {}".format(sPart)

        super().__init__(
            sMsg=sMsg,
            sType="proc-lambda-part",
            xData=sPart,
            xSelect=None,
            xChildEx=xChildEx,
        )

    # enddef


# endclass
