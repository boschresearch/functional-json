#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \ison\run.py
# Created Date: Tuesday, February 15th 2022, 10:16:25 am
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
import sys

from .core.cls_parser import CParser as Parser
from .core.cls_parser_error import CParserError
from .util import io, text, data
from pathlib import Path


######################################################################
def ToString(_dicData: dict, iIndent=4):
    return text.ToString(_dicData, iIndent=iIndent)


# enddef


######################################################################
def Run(*, xData, dicConstVars={}, sResultKey=None, bStripVars=True, sImportPath=None, bPrintWarnings=False):

    try:
        if isinstance(xData, str):
            dicData = io.decode_json(xData)
        else:
            dicData = xData
        # endif

        xParse = Parser(dicConstVars)
        xResult = xParse.Process(dicData, sImportPath=sImportPath)

        xWarnings = xParse.GetWarnings()
        if bPrintWarnings is True and xWarnings.bHasWarnings is True:
            sys.stderr.write("WARNINGS:\n")
            sys.stderr.write(str(xWarnings))
            sys.stderr.flush()
        # endif

        if sResultKey is not None:
            if not isinstance(xResult, dict):
                raise RuntimeError(
                    "Result key '{}' given, but result is not a dictionary:\n{}".format(
                        sResultKey, io.encode_json(xResult, iIndent=4)
                    )
                )
            # endif

            if sResultKey not in xResult:
                raise RuntimeError(
                    "Result key '{}' not found in result:\n{}".format(
                        sResultKey, io.encode_json(xResult, iIndent=4)
                    )
                )
            # endif

            xResult = xResult[sResultKey]
        # endif

        # strip all variable definition blocks from result data
        # if flag is set.
        if bStripVars is True and isinstance(xResult, dict):
            xResult = data.StripVarsFromData(xResult)
        # endif

        return xResult

    except Exception as xEx:
        if isinstance(xEx, CParserError):
            sText = xEx.ToString()
        else:
            sText = str(xEx)
        # endif

        sMsg = "Error running ISON parser:\n{}".format(sText)
        raise RuntimeError(sMsg)
    # endtry


# enddef


######################################################################
def RunCli():
    try:
        import argparse

        xArgParse = argparse.ArgumentParser(description="Run ISON parsing")

        xArgParse.add_argument(
            "filename_in",
            nargs="?",
            default="-",
            help="The file to parse. If not specified or set to '-', uses stdin.",
        )

        xArgParse.add_argument(
            "filename_out",
            nargs="?",
            default="-",
            help="The file to write the output to. If not specified or set to '-' uses stdout",
        )

        xArgParse.add_argument(
            "-i", "--indent-output", nargs=1, dest="indent", default=None
        )
        xArgParse.add_argument(
            "-r", "--result-key", nargs=1, dest="reskey", default=None
        )
        xArgParse.add_argument("--strip-vars", dest="stripvars", action="store_true")
        xArgParse.add_argument("-a", "--args", nargs="*", dest="vars")
        xArgs = xArgParse.parse_args()

        try:
            if xArgs.indent is None:
                iIndent = -1
            else:
                iIndent = int(xArgs.indent[0])
            # endif
        except Exception:
            raise RuntimeError(
                "Given indent '{}' is not an integer".format(xArgs.indent)
            )
        # endtry

        sFilenameOut = xArgs.filename_out
        if sFilenameOut == "-":
            sFilenameOut = None
        # endif

        try:
            sTextIn = None
            bUsesStdIn = False
            sFpIn = xArgs.filename_in
            if sFpIn == "-":
                bUsesStdIn = True
                sFpIn = "<stdin>"
                sTextIn = sys.stdin.read()
            else:
                pathFileIn = Path(io.ToAbsPath(sFpIn))
                sFpIn = pathFileIn.as_posix()
                if not pathFileIn.exists():
                    raise RuntimeError("Input file '{}' does not exist".format(sFpIn))
                # endif
                with open(sFpIn, "r") as xFile:
                    sTextIn = xFile.read()
                # endwith
            # endif
            xData = io.decode_json(sTextIn)
        except Exception as xEx:
            raise RuntimeError(
                "Error loading file '{}' as json/json5\n{}".format(sFpIn, str(xEx))
            )
        # endtry

        dicConstVars = {}
        dicRun = dicConstVars["run"] = {}
        lVars = dicRun["args"] = []
        dicVars = dicRun["kwargs"] = {}
        dicFile = dicRun["file"] = {}

        dicRun["cwd"] = os.getcwd()

        sImportPath = None
        if bUsesStdIn is True:
            dicFile["source"] = "stdin"

        else:
            sImportPath = pathFileIn.parent.as_posix()
            dicFile = {
                "source": "local",
                "path": pathFileIn.as_posix(),
                "dir": pathFileIn.parent.as_posix(),
                "folder": pathFileIn.parent.name,
                "ext": pathFileIn.suffix,
                "name": pathFileIn.name,
                "basename": pathFileIn.stem,
            }
        # endif

        if xArgs.vars is not None:

            for iIdx, sVar in enumerate(xArgs.vars):
                lParts = text.SplitArgs(sVar, sSplitChar="=")[0]

                if len(lParts) == 1:
                    sKey = None
                    sValue = lParts[0].strip(" '")
                else:
                    sKey = lParts[0].strip(" '")
                    sValue = lParts[1].strip(" '")
                # endif

                if sValue == "-":
                    if bUsesStdIn is True:
                        raise RuntimeError("'<stdin>' already used to read ison file")
                    # endif

                    sValue = sys.stdin.read()
                # endif

                if sKey is None:
                    lVars.append(sValue)
                else:
                    dicVars[sKey] = sValue
                # endif
            # endfor
        # endif

        if xArgs.reskey is not None:
            sResultKey = xArgs.reskey[0]
        else:
            sResultKey = None
        # endif

        xResult = Run(
            xData=xData,
            dicConstVars=dicConstVars,
            sResultKey=sResultKey,
            sImportPath=sImportPath,
            bStripVars=xArgs.stripvars,
        )

        if isinstance(xResult, str):
            sResult = xResult
        else:
            sResult = io.encode_json(xResult, iIndent=iIndent)
        # endif

        if sFilenameOut is not None:
            with open(sFilenameOut, "w") as xFile:
                xFile.write(sResult)
            # endwith

        else:
            # print to stdout
            sys.stdout.write(sResult)
        # endif

        return 0

    except Exception as xEx:
        sys.stderr.write(str(xEx))
    # endtry

    return 1


# enddef
