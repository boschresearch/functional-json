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

import os
from pathlib import Path
from glob import glob

from ..util import io
from ..util import convert
from ..core.cls_parser_error import CParserError, CParserError_FuncMessage
from ..core import var_nt


def tooltip(sTooltip):
    def inner(func):
        func.tooltip = sTooltip
        return func

    return inner


################################################################################
@tooltip(
    "Read file passed as filename. If the extension is '.json', '.json5' or '.ison', the file is converted to a data object."
)
def ReadFile_Text(_xParser, _lArgs, _lArgIsProc, *, sFuncName):

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
    if not isinstance(xArg, str):
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="Expect a filename as argument, but an object of type '{}' was received.".format(
                CParserError.Typename(xArg)
            ),
        )
    # endif

    try:
        pathFile = Path(os.path.expandvars(xArg)).expanduser()
        if not pathFile.is_absolute():
            pathImport = _xParser.GetImportPath()
            if pathImport is None:
                raise CParserError_FuncMessage(
                    sFunc=sFuncName,
                    sMsg="Import path not specified to resolve relative path: {}".format(pathFile.as_posix()),
                )
            # endif
            pathFile = _xParser.GetImportPath() / pathFile
        # endif
    except Exception as xEx:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="Error resolving file path of '{}':\n> {}".format(xArg, str(xEx)),
        )
    # endtry

    try:
        if pathFile.suffix in ["", ".json", ".json5", ".ison"]:
            xData = io.LoadJson(pathFile)
        else:
            if not pathFile.exists():
                raise CParserError_FuncMessage(sFunc=sFuncName, sMsg="File not found: {}".format(pathFile.as_posix()))
            # endif

            with open(pathFile, "r") as xFile:
                xData = xFile.read()
            # endwith
        # endif
    except Exception as xEx:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="Error reading from file '{}':\n> {}".format(pathFile.as_posix(), str(xEx)),
        )
    # endtry

    return xData, False


# enddef


################################################################################
@tooltip(
    "Write data in argument 2 to file with path given in argument 1. Optional arguments are boolean create-path and integer json-indent"
)
def WriteFile_Text(_xParser, _lArgs, _lArgIsProc, *, sFuncName):

    if not all(_lArgIsProc):
        return None, False
    # endif

    iArgCnt = len(_lArgs)

    if iArgCnt < 2:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="Expect at least 2 arguments but {0} were given".format(iArgCnt),
        )
    # endif

    xArg = _lArgs[0]
    if not isinstance(xArg, str):
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="Expect a filename as first argument, but an object of type '{}' was received.".format(
                CParserError.Typename(xArg)
            ),
        )
    # endif

    iJsonIndent = -1
    bCreatePath = False

    if iArgCnt > 2:
        try:
            for sArg in _lArgs[2:]:
                dicData = var_nt.GetData(sArg)
                if dicData is None:
                    raise CParserError_FuncMessage(
                        sFunc=sFuncName,
                        sMsg="Malformed optional argument: {}".format(sArg),
                    )
                # endif

                for sKey in dicData:
                    sValue = dicData[sKey]

                    if sKey == "create-path":
                        bCreatePath = convert.ToBool(sValue)

                    elif sKey == "json-indent":
                        iJsonIndent = convert.ToInt(sValue)

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

    try:
        pathFile = Path(os.path.expandvars(xArg)).expanduser()
        if not pathFile.is_absolute():
            sMainPath: str = _xParser.GetImportPath()
            if sMainPath is None:
                pathFile = Path.cwd() / pathFile
            else:
                pathFile = sMainPath / pathFile
            # endif
        # endif
    except Exception as xEx:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="Error resolving file path of '{}':\n> {}".format(xArg, str(xEx)),
        )
    # endtry

    xData = _lArgs[1]
    if not isinstance(xData, str):
        try:
            sData = io.encode_json(xData, iIndent=iJsonIndent)

        except Exception as xEx:
            raise CParserError_FuncMessage(
                sFunc=sFuncName,
                sMsg="Error converting argument to string",
                xChildEx=xEx,
            )
        # endtry
    else:
        sData = xData
    # endif

    try:
        if bCreatePath is True:
            pathFile.parent.mkdir(parents=True, exist_ok=True)
        # endif

        with open(pathFile, "w") as xFile:
            xFile.write(sData)
        # endwith
    except Exception as xEx:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="Error writing to file '{}'".format(pathFile.as_posix()),
            xChildEx=xEx,
        )
    # endtry

    return pathFile.as_posix(), False


# enddef


################################################################################
@tooltip("Return all files in directory as list. Wildcards in the 'glob' style are supported.")
def DirectoryList(_xParser, _lArgs, _lArgIsProc, *, sFuncName):

    if not all(_lArgIsProc):
        return None, False
    # endif

    iArgCnt = len(_lArgs)

    if iArgCnt != 1:
        raise Exception("Function {0} expects exactly 1 argument but {1} were given".format(sFuncName, iArgCnt))
    # endif

    sPath = _lArgs[0]
    if not isinstance(sPath, str):
        raise Exception("Function {0}: First parameter has to be a string".format(sFuncName))
    # endif

    try:
        pathDir = Path(io.ToNormPath(sPath))
        if not pathDir.is_absolute():
            pathDir = _xParser.GetImportPath() / pathDir
        # endif
    except Exception as xEx:
        raise CParserError_FuncMessage(
            sFunc=sFuncName,
            sMsg="Error resolving path '{}':\n> {}.".format(sPath, str(xEx)),
        )
    # endtry

    lPaths = glob(pathDir.as_posix(), recursive=True)
    if lPaths is not None:
        xResult = [io.ToNormPath(x) for x in lPaths]
    else:
        xResult = None
    # endif

    return xResult, False


# enddef


################################################################################
def _DoPathFunc(_xPath, _sFunc, *, sFuncName):

    xResult = None

    if isinstance(_xPath, str):
        pathX = Path(io.ToNormPath(_xPath))

    elif isinstance(_xPath, list):
        xResult = []
        for sEl in _xPath:
            xResult.append(_DoPathFunc(sEl, _sFunc, sFuncName=sFuncName))
        # endfor
        return xResult

    else:
        raise CParserError_FuncMessage(sFunc=sFuncName, sMsg="Invalid argument type")
    # endif

    if _sFunc == "parts":
        xResult = list(pathX.parts)

    elif _sFunc == "info":
        xResult = {
            "posix": pathX.as_posix(),
            "suffixes": pathX.suffixes,
            "parents": [x.as_posix() for x in pathX.parents],
            "name": pathX.name,
            "stem": pathX.stem,
        }

    elif _sFunc == "parent":
        xResult = pathX.parent.as_posix()

    elif _sFunc == "parents":
        xResult = [x.as_posix() for x in pathX.parents]

    elif _sFunc == "suffix":
        xResult = pathX.suffix

    elif _sFunc == "suffixes":
        xResult = pathX.suffixes

    elif _sFunc == "name":
        xResult = pathX.name

    elif _sFunc == "stem":
        xResult = pathX.stem
    # endif

    return xResult


# enddef


################################################################################
@tooltip("Various path functions: path.info, .name, .parent, .parents, .parts, .stem, .suffix, .suffixes")
def PathFuncGrp(_xParser, _lArgs, _lArgIsProc, *, sFuncName, lFuncParts):

    if not all(_lArgIsProc):
        return None, False
    # endif

    lSubFuncs = [
        "info",
        "name",
        "parent",
        "parents",
        "parts",
        "stem",
        "suffix",
        "suffixes",
    ]
    if len(lFuncParts) < 2 or any((x not in lSubFuncs for x in lFuncParts[1:])):
        raise RuntimeError(f"Function {sFuncName} not defined")
    # endif

    iArgCnt = len(_lArgs)

    if iArgCnt != 1:
        raise RuntimeError("Function {0} expects exactly 1 argument but {1} were given".format(sFuncName, iArgCnt))
    # endif

    sPath = _lArgs[0]
    if not isinstance(sPath, str) and not isinstance(sPath, list):
        raise RuntimeError("Function {0}: First parameter has to be a string or list".format(sFuncName))
    # endif

    xResult = sPath
    for sSubFunc in lFuncParts[1:]:
        xResult = _DoPathFunc(xResult, sSubFunc, sFuncName=sFuncName)
    # endfor

    return xResult, False


# enddef


################################################################################
__ison_functions__ = {
    "read": {"funcExec": ReadFile_Text, "bLiteralArgs": False},
    "write": {"funcExec": WriteFile_Text, "bLiteralArgs": False},
    "dir": {"funcExec": DirectoryList, "bLiteralArgs": False},
    "path.*": {"funcExec": PathFuncGrp, "bLiteralArgs": False},
}
