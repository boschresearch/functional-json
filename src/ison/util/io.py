#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \ison\file.py
# Created Date: Tuesday, February 15th 2022, 9:29:20 am
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

import re
import os

try:
    import pyjson5
except Exception:
    print("Module 'pyjson5' not installed. JSON5 files will not be supported.")
# endtry

import json
from pathlib import Path
from . import path

from ..core.cls_parser_error import CParserError, CParserError_Message


#######################################################################
def ToAbsPath(_sFilePath):
    return os.path.normpath(
        os.path.abspath(os.path.expandvars(os.path.expanduser(_sFilePath)))
    )


# enddef

#######################################################################
def ToNormPath(_sPath, bAsPosix=True):

    sNormPath = os.path.normpath(os.path.expandvars(os.path.expanduser(_sPath)))

    if bAsPosix is True:
        sNormPath = Path(sNormPath).as_posix()
    # endif
    return sNormPath


# enddef

#######################################################################
# Load JSON file from path
def decode_json_file(_sFilePath):

    with open(_sFilePath, "r") as xFile:
        if pyjson5 is not None:
            dicData = pyjson5.decode_io(xFile)
        else:
            dicData = json.load(xFile)
        # endif
    # endwith

    return dicData


# enddef


#######################################################################
# save JSON file from relative path to script path
def encode_json_file(_sFilePath, _dicData, iIndent=-1):

    with open(_sFilePath, "w") as xFile:
        if pyjson5 is not None and (iIndent < 0 or _sFilePath.endswith(".json5")):
            pyjson5.encode_io(_dicData, xFile, supply_bytes=False)
        else:
            json.dump(_dicData, xFile, indent=iIndent)
        # endif
    # endwith


# enddef


#######################################################################
def encode_json(_xData, iIndent=-1):

    if pyjson5 is not None and iIndent < 0:
        sData = pyjson5.encode(_xData)
    else:
        sData = json.dumps(_xData, indent=iIndent)
    # endif

    return sData


# enddef


#######################################################################
def decode_json(_sData):

    if pyjson5 is not None:
        xData = pyjson5.decode(_sData)
    else:
        xData = json.loads(_sData)
    # endif

    return xData


# enddef


#######################################################################
# Load JSON file from path
def LoadJson(_xFilePath) -> dict:

    pathFile = path.MakeNormPath(_xFilePath)

    if len(pathFile.suffix) == 0:
        pathTest = pathFile.parent / (pathFile.name + ".json")
        if not pathTest.exists():
            pathTest = pathFile.parent / (pathFile.name + ".json5")
            if not pathTest.exists():
                pathTest = pathFile.parent / (pathFile.name + ".ison")
                if not pathTest.exists():
                    raise CParserError_Message(
                        sMsg="File not found: {}[.json, .json5, .ison]".format(
                            pathFile.as_posix()
                        )
                    )
                # endif
            # endif
        # endif
        pathFile = pathTest

    elif not pathFile.exists():
        raise CParserError_Message(
            sMsg="File not found: {}".format(pathFile.as_posix())
        )
    # endif

    if pyjson5 is None:
        return decode_json_file(pathFile.as_posix())
    # endif

    try:
        with pathFile.open("r") as xFile:
            dicData = pyjson5.decode_io(xFile)
        # endwith
    except pyjson5.Json5IllegalCharacter as xEx:
        print(xEx.message)
        xMatch = re.search(r"near\s+(\d+),", xEx.message)
        if xMatch is None:
            raise CParserError_Message(
                sMsg=CParserError.ListToString(
                    [
                        "Illegal character encountered while parsing JSON file",
                        xEx.message,
                        pathFile.as_posix(),
                    ]
                )
            )
        # endif
        iCharPos = int(xMatch.group(1))
        sText = pathFile.read_text()
        lLines = sText.split("\n")
        iCharCnt = 0
        iLinePos = len(lLines) - 1

        for iLineIdx, sLine in enumerate(lLines):
            iCharCnt += len(sLine) + 1
            if iCharCnt >= iCharPos:
                iLinePos = iLineIdx
                break
            # endif
        # endfor

        # From character position, subtract length of line with error and
        # the numer of lines before this line, to subtract the newline characters
        iCharPosInLine = min(
            len(lLines[iLinePos]) - 1,
            max(0, iCharPos - (iCharCnt - len(lLines[iLinePos]))),
        )

        lMsg = [
            "Unexpected character '{}' encountered in line {} at position {}".format(
                xEx.character, iLinePos + 1, iCharPosInLine + 1
            )
        ]
        iLineStart = max(0, iLinePos - 1)
        iLineEnd = min(len(lLines) - 1, iLinePos + 1)
        for iLineIdx in range(iLineStart, iLineEnd + 1):
            sLine = lLines[iLineIdx]
            if iLineIdx == iLinePos:
                sMsg = ">{:3d}<: ".format(iLineIdx + 1)
                sMsg += sLine[0:iCharPosInLine]
                sMsg += ">{}<".format(sLine[iCharPosInLine])
                sMsg += sLine[iCharPosInLine + 1 :]
            else:
                sMsg = " {:3d} :  {}".format(iLineIdx + 1, sLine)
            # endif
            lMsg.append(sMsg)
        # endfor
        raise CParserError_Message(
            sMsg="Error parsing JSON file: {}{}".format(
                pathFile.as_posix(), CParserError.ListToString(lMsg)
            )
        )
    # endtry

    return dicData


# enddef


#######################################################################
# save JSON file from relative path to script path
def SaveJson(_xFilePath, _dicData, iIndent=-1):

    pathFile = path.MakeNormPath(_xFilePath)

    with pathFile.open("w") as xFile:
        if iIndent < 0 or pathFile.suffix == ".json5" or pathFile.suffix == ".ison":
            pyjson5.encode_io(_dicData, xFile, supply_bytes=False)
        else:
            json.dump(_dicData, xFile, indent=iIndent)
        # endif
    # endwith


# enddef
