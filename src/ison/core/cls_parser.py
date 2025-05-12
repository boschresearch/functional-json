#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \cathy\logconfig.py
# Created Date: Monday, November 23rd 2020, 4:11:28 pm
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

import copy
import json
import os
import sys
from typing import Optional, Union
from types import ModuleType
from pathlib import Path
from datetime import datetime

from ..util import data
from ..util import text
from ..util import io
from ..util import path
from .. import func
from .cls_parser_error import (
    CParserError,
    CParserError_Message,
    CParserError_DictSel,
    CParserError_DictItem,
    CParserError_ListSel,
    CParserError_ProcArgStr,
    CParserError_ProcFunc,
    CParserError_ProcFuncArgs,
    CParserError_ProcKey,
    CParserError_ProcRefPath,
    CParserError_ProcStr,
    CParserError_StrMatch,
    CParserError_KeyStrMatch,
    CParserError_ProcArgListElement,
)
from . import lambda_parser
from . import var_nt

from .defines import (
    reVarStart,
    rePureVar,
    reSlice,
    reLambdaFunc,
    reLambdaPar,
    reNamedArg,
    reLiteralArg,
    reUnrollArg,
    reTupleArg,
)
from .cls_parser_trace import CWarning, CWarningList, EWarningType, EParseContext, CParseContextElement


# ###################################################################################
"""Implementation of ISON parsing language.
"""


class CParser:
    @property
    def dicFuncStorage(self) -> dict:
        return self.dicVarData["@func-storage"]

    # enddef

    @property
    def dicVarRtv(self) -> dict:
        return self.dicVarData["@rtv"]

    # enddef

    @property
    def dicVarGlo(self) -> dict:
        return self.dicVarData["@glo"]

    # enddef

    @property
    def dicVarLoc(self) -> dict:
        return self.dicVarData["@loc"]

    # enddef

    @property
    def lVarLocStack(self) -> list[dict]:
        return self.dicVarData["@loc-s"]

    # enddef

    @property
    def setVarRtvEval(self) -> set:
        return self.dicVarData["@rtv-eval"]

    # enddef

    @property
    def setVarGloEval(self) -> set:
        return self.dicVarData["@glo-eval"]

    # enddef

    @property
    def setVarLocEval(self) -> set:
        return self.dicVarData["@loc-eval"]

    # enddef

    @property
    def lVarLocEvalStack(self) -> list[set]:
        return self.dicVarData["@loc-eval-s"]

    # enddef

    @property
    def dicVarFuncGlo(self) -> dict:
        return self.dicVarData["@func-glo"]

    # enddef

    @property
    def dicVarFuncLoc(self) -> dict:
        return self.dicVarData["@func-loc"]

    # enddef

    @property
    def lVarFuncLocStack(self) -> list[dict]:
        return self.dicVarData["@func-loc-s"]

    # enddef

    @property
    def bIsFullyProcessed(self) -> bool:
        return self._bIsFullyProcessed

    # enddef

    ################################################################################
    def __init__(
        self,
        _dicConstVars: dict,
        dicRefVars: dict = None,
        sImportPath: str = None,
        dicRtVars: dict = None,
        setRtVarsEval: set = None,
        xParser: "CParser" = None,
    ):
        if isinstance(_dicConstVars, dict):
            self.dicVarData = copy.deepcopy(_dicConstVars)
        else:
            self.dicVarData = {}
        # endif

        if isinstance(dicRefVars, dict):
            self.dicVarData.update(dicRefVars)
        # endif

        self.bIgnoreImport = False

        self.sImportPath = None
        if sImportPath is not None:
            if os.path.exists(sImportPath):
                self.sImportPath = sImportPath
            # endif
        # endif

        self.Clear()
        self.ClearVarRuntime()
        self.AddRuntimeVars(_dicRtVars=dicRtVars, _setRtVarsEval=setRtVarsEval)

        # Initialize internal storage for functions
        self.dicVarData["@func-storage"] = {}

        # Copy state of given parser instance, if any.
        if isinstance(xParser, CParser):
            data.UpdateDict(
                self.dicVarData, xParser.dicVarData, "parser initialization", bAllowOverwrite=True, bPrintWarnings=False
            )

        # endif

        # Reset at start of parsing. If at least one variable could not be processed,
        # this variable is set to False
        self._bIsFullyProcessed: bool = False

        self.pathLog: Path = None

        # RegEx for start of variable expression
        self.reVarStart = reVarStart

        # RegEx for a pure variable
        self.rePureVar = rePureVar

        # RegEx for slicing of lists
        self.reSlice = reSlice

        # RegEx for Lambda function
        self.reLambdaFunc = reLambdaFunc

        # Initialize Function Pointers
        self.dicFunc = {}
        self.lLiteralArgsFuncs = []

        self.lValidVarTags = [
            "__runtime_vars__",
            "__globals__",
            "__locals__",
            "__eval_globals__",
            "__eval_locals__",
            "__func_globals__",
            "__func_locals__",
        ]
        self.lValidExtraTags = [
            "__includes__",
            "__platform__",
            "__data__",
            "__pre__",
            "__lambda__",
        ]
        self.lValidSpecialTags = []
        self.lValidSpecialTags.extend(self.lValidVarTags)
        self.lValidSpecialTags.extend(self.lValidExtraTags)
        self.lValidSpecialTagsInVars = ["__includes__", "__platform__"]

        self.xWarnings: CWarningList = CWarningList()
        self.lParseContext: list[CParseContextElement] = []

        # Register base functions
        for sModFunc in dir(func):
            modFunc = getattr(func, sModFunc)
            if isinstance(modFunc, ModuleType) and hasattr(modFunc, "__ison_functions__"):
                self.RegisterFunctionModule(modFunc)
            # endif
        # endfor

        self.ProvideVariables()

    # enddef

    ################################################################################
    def UpdateConstVars(self, _dicConstVars: dict, *, _bAllowOverwrite: bool = False, _bPrintWarnings: bool = False):
        if isinstance(_dicConstVars, dict):
            data.UpdateDict(
                self.dicVarData,
                _dicConstVars,
                "constant variables",
                bAllowOverwrite=_bAllowOverwrite,
                bPrintWarnings=_bPrintWarnings,
            )
        # endif

    # enddef

    ################################################################################
    def RegisterFunctionModule(self, _xModule):
        if not hasattr(_xModule, "__ison_functions__"):
            raise Exception("Given function module does not have function declarations in '__ison_functions__'")
        # endif

        if not isinstance(_xModule.__ison_functions__, dict):
            raise Exception("Element '__ison_functions__' of given module is not a dictionary")
        # endif

        for sFunc, xExec in _xModule.__ison_functions__.items():
            if isinstance(xExec, dict) is True:
                if xExec.get("bLiteralArgs", False) is True:
                    self.lLiteralArgsFuncs.append(sFunc)
                # endif
                funcExec = xExec.get("funcExec")
                if funcExec is None:
                    raise RuntimeError(f"No implementation defined for function '{sFunc}'")
                # endif
                self.dicFunc[sFunc] = funcExec
            else:
                self.dicFunc[sFunc] = xExec
            # endif
        # endfor

    # enddef

    ################################################################################
    def Clear(self):
        self.ClearVariables()
        self.dicImport = {}

    # enddef

    ################################################################################
    def ClearVariables(self):
        self.ClearVarLocals()
        self.ClearVarGlobals()
        self.ClearFuncLocals()
        self.ClearFuncGlobals()

    # enddef

    ################################################################################
    def SetLogFilePath(
        self, *, _xPath: Union[Path, list, str, tuple] = None, _bCreate: bool = False, _bEnable: bool = True
    ) -> Path:
        if _bEnable is False:
            self.pathLog = None
            return
        # endif

        if _xPath is None:
            pathLog = Path.cwd()
        else:
            pathLog = path.MakeNormPath(_xPath)
        # endif
        pathLog = pathLog.absolute()

        if len(pathLog.suffix) == 0:
            dtNow = datetime.now()
            sDT = dtNow.strftime("ison-log_%Y-%m-%d_%H-%M-%S.txt")
            pathLog /= sDT
        # endif

        if _bCreate is True:
            pathLog.parent.mkdir(exist_ok=True, parents=True)
        # endif

        if not pathLog.parent.exists():
            raise CParserError_Message(sMsg=f"Path for logging does not exist: {(pathLog.as_posix())}")
        # endif

        self.pathLog = pathLog
        return self.pathLog

    # enddef

    ################################################################################
    def LogString(self, _sText: str):
        if self.pathLog is None:
            sys.stdout.write(_sText + "\n")
            sys.stdout.flush()

        elif isinstance(self.pathLog, Path):
            with self.pathLog.open("a") as fileLog:
                fileLog.write(_sText + "\n")
            # endwith

        else:
            raise CParserError_Message(sMsg="Invalid type of member 'pathLog'")
        # endif

    # enddef

    ################################################################################
    def ProvideVariables(self):
        if "@rtv" not in self.dicVarData:
            self.ClearVarRuntime()
        # endif

        if "@glo" not in self.dicVarData:
            self.ClearVarGlobals()
        # endif

        if "@loc" not in self.dicVarData:
            self.ClearVarLocals()
        # endif

        if "@func-glo" not in self.dicVarData:
            self.ClearFuncGlobals()
        # endif

        if "@func-loc" not in self.dicVarData:
            self.ClearFuncLocals()
        # endif

    # enddef

    ################################################################################
    def AddRuntimeVars(self, *, _dicRtVars: dict, _setRtVarsEval: set, _bCopyData: bool = False):
        if isinstance(_dicRtVars, dict) and len(_dicRtVars) > 0:
            data.UpdateDict(
                self.dicVarRtv,
                _dicRtVars,
                "runtime vars",
                bAllowOverwrite=True,
                bPrintWarnings=False,
                bIgnoreSpecialVars=True,
                bCopyData=_bCopyData,
            )

            # Newly added locals are removed from evaluated set
            setVarRtvEval: set = self.setVarRtvEval
            for sKey in _dicRtVars:
                if sKey in setVarRtvEval:
                    setVarRtvEval.remove(sKey)
                # endif
            # endfor

            if isinstance(_setRtVarsEval, set):
                setVarRtvEval.update(_setRtVarsEval)
            # endif

        # endif

    # enddef

    ################################################################################
    def GetRuntimeVars(self, _bCopy: bool = True):
        if _bCopy is True:
            return copy.deepcopy(self.dicVarRtv)
        else:
            return self.dicVarRtv
        # endif

    # enddef

    ################################################################################
    def GetRuntimeVarEvalSet(self, _bCopy: bool = True):
        if _bCopy is True:
            return copy.deepcopy(self.setVarRtvEval)
        else:
            return self.setVarRtvEval
        # endif

    # enddef

    ################################################################################
    def ClearVarLocals(self):
        self.dicVarData["@loc"] = {}
        self.dicVarData["@loc-eval"] = set()
        self.dicVarData["@loc-s"] = []
        self.dicVarData["@loc-eval-s"] = []

    # enddef

    ################################################################################
    def ClearVarGlobals(self):
        self.dicVarData["@glo"] = {}
        self.dicVarData["@glo-eval"] = set()

    # enddef

    ################################################################################
    def ClearVarRuntime(self):
        self.dicVarData["@rtv"] = {}
        self.dicVarData["@rtv-eval"] = set()

    # enddef

    ################################################################################
    def ClearFuncLocals(self):
        self.dicVarData["@func-loc"] = {}
        self.dicVarData["@func-loc-s"] = []

    # enddef

    ################################################################################
    def ClearFuncGlobals(self):
        self.dicVarData["@func-glo"] = {}

    # enddef

    ################################################################################
    def IsIgnoreImport(self):
        return self.bIgnoreImport

    # enddef

    ################################################################################
    def GetImportPath(self):
        return self.sImportPath

    # enddef

    ################################################################################
    def GetVarData(self):
        return self.dicVarData

    # enddef

    ################################################################################
    def GetWarnings(self) -> CWarningList:
        return self.xWarnings

    # enddef

    ################################################################################
    def AddWarning(self, _eType: EWarningType, _sKey: str):
        sCtx = self._GetParseContextString()

        sShortCtx: str = None
        if _eType == EWarningType.UNDEF_VAR:
            # Store information that variable could not be fully processed
            lParentVars: str = []
            for xPc in reversed(self.lParseContext):
                if xPc.eContext == EParseContext.VAR:
                    lParentVars.append(xPc.sValue)
                # endif
            # endfor

            if len(lParentVars) > 0:
                sShortCtx = "required by " + " < ".join([f"'{x}'" for x in lParentVars])
            # endif
        # endif

        self.xWarnings.Add(CWarning(_eType=_eType, _sKey=_sKey, _sCtx=sCtx, _sShortCtx=sShortCtx))

    # enddef

    ################################################################################
    def _EnterParseContext(self, _eCtx: EParseContext, _sValue: str = "", _lData: list = None, _iData: int = None):
        self.lParseContext.append(CParseContextElement(eContext=_eCtx, sValue=_sValue, lData=_lData, iData=_iData))

    # enddef

    ################################################################################
    def _ExitParseContext(self):
        if len(self.lParseContext) > 0:
            self.lParseContext.pop(-1)
        # endif

    # enddef

    ################################################################################
    def _GetParseContextString(self):
        sCtx = ""
        xPC: CParseContextElement

        for iIdx, xPC in enumerate(self.lParseContext):
            sEl = ""
            if xPC.eContext == EParseContext.DICT:
                sEl = "dict"

            elif xPC.eContext == EParseContext.DICT_EL:
                sEl = f"[{(xPC.sValue)}]"

            elif xPC.eContext == EParseContext.FGLO:
                sEl = "__func_globals__"

            elif xPC.eContext == EParseContext.FLOC:
                sEl = "__func_locals__"

            elif xPC.eContext == EParseContext.FUNC:
                lArgs = []
                for xArg in xPC.lData:
                    sArg = str(xArg)
                    if len(sArg) > 8:
                        sArg = sArg[:8] + "..."
                    # endif
                    lArgs.append(sArg)
                # endfor
                sArgs = ", ".join(lArgs)
                sEl = f"${(xPC.sValue)}{{{sArgs}}}"

            elif xPC.eContext == EParseContext.ARG:
                sEl = f"arg: {(xPC.sValue)}"

            elif xPC.eContext == EParseContext.RTV:
                sEl = "__runtime_vars__"

            elif xPC.eContext == EParseContext.GLO:
                sEl = "__globals__"

            elif xPC.eContext == EParseContext.LOC:
                sEl = "__locals__"

            elif xPC.eContext == EParseContext.PLAT:
                sEl = "__platform__"

            elif xPC.eContext == EParseContext.PLAT_DATA:
                sEl = "__data__"

            elif xPC.eContext == EParseContext.PRE:
                sEl = "__pre__"

            elif xPC.eContext == EParseContext.REF_PATH:
                sEl = f"{(xPC.sValue)}"

            elif xPC.eContext == EParseContext.INC:
                sEl = f"include({(xPC.sValue)})"

            elif xPC.eContext == EParseContext.VAR:
                sEl = f"var: {(xPC.sValue)}"

            # elif xPC.eContext == EParseContext.MATCH:

            else:
                sEl = "?"
            # endif

            sCtx += f"| {(iIdx+1)}: {sEl}\n"
        # endfor

        return sCtx

    # enddef

    ################################################################################
    # Get Reference string to element in Var Data
    def GetVarDataRef(self, _lPath, *, bLiteral=False):
        # Check whether path exists
        xEl = self.dicVarData
        for sKey in _lPath:
            xEl = xEl.get(sKey)
            if xEl is None:
                raise CParserError_Message(
                    sMsg="Element '{0}' of path '{1}' does not exist when creating reference".format(
                        sKey, ":".join(_lPath)
                    )
                )
            # endif
        # endfor

        if bLiteral is True:
            return "${{{0}:}}".format(":".join(_lPath))
        else:
            return "${{{0}}}".format(":".join(_lPath))
        # endif

    # enddef

    ################################################################################
    def ReplacePureVars(self, _xData):
        """Replace pure variables only. No processing of function or nested variables.

        Args:
            _xData (dict): The dictionary where to replace variables.
        """

        sData = json.dumps(_xData)
        sNewData = ""

        iStart = 0
        for xMatch in self.rePureVar.finditer(sData):
            sToken = xMatch.group("var")
            if sToken is None:
                sToken = xMatch.group("pure")
            # endif
            xVar = self.dicVarData.get(sToken)
            if xVar is not None:
                sVar = text.ToString(xVar)
                sNewData += sData[iStart : xMatch.start()]
                sNewData += sVar
                iStart = xMatch.end()
            # endif
        # endfor

        sNewData += sData[iStart:]
        xNewData = json.loads(sNewData)

        return xNewData

    # enddef

    ################################################################################
    def Process(
        self,
        _xData,
        sImportPath=None,
        lProcessPaths=None,
        bPreProcessOnly=False,
        bIgnoreImport=False,
        dicGlobals=None,
        dicLocals=None,
        dicEvalGlobals=None,
        dicEvalLocals=None,
        dicFuncGlobals=None,
        dicFuncLocals=None,
        dicConstVars=None,
        bInPlace: bool = False,
    ):
        sSelfIgnoreImport = self.bIgnoreImport
        self.bIgnoreImport = bIgnoreImport

        sSelfImportPath = self.sImportPath

        if sImportPath is not None:
            if os.path.exists(sImportPath):
                self.sImportPath = sImportPath
            # endif
        # endif

        self.xWarnings.Clear()
        self.lParseContext = []

        lProcPathLists = None
        lProcPathResults = []
        if lProcessPaths is not None:
            if not isinstance(lProcessPaths, list):
                raise CParserError_Message(sMsg="Parameter 'lProcessPaths' has to be a list of strings")
            # endif
            lProcPathLists = [x.split("/") for x in lProcessPaths]
        # endif

        self._bIsFullyProcessed: bool = True

        self.ClearVarLocals()
        self.ClearFuncLocals()

        if isinstance(dicConstVars, dict):
            data.UpdateDict(self.dicVarData, dicConstVars, "set constant variables", bAllowOverwrite=True)
        # endif

        if bInPlace is False:
            xData = copy.deepcopy(_xData)
        else:
            xData = _xData
        # endif

        data.AddVarsToData(
            xData,
            dicLocals=dicLocals,
            dicGlobals=dicGlobals,
            dicEvalLocals=dicEvalLocals,
            dicEvalGlobals=dicEvalGlobals,
            dicFuncGlobals=dicFuncGlobals,
            dicFuncLocals=dicFuncLocals,
        )

        try:
            if isinstance(xData, dict):
                # add the xData to top level variable @this
                self.dicVarData["@top"] = xData

                if lProcPathLists is None:
                    self._PreProcess(xData)
                # endif
            # endif

            if bPreProcessOnly:
                xResult = xData
            else:
                if lProcPathLists is not None:
                    for lPath in lProcPathLists:
                        xResult, bIsProcessed = self.InnerProcess(xData, lPath=lPath)
                        lProcPathResults.append(xResult)
                    # endfor

                else:
                    xResult, bIsProcessed = self.InnerProcess(xData)

                # endif
            # endif
        except CParserError as xEx:
            xEx.xWarnings = copy.deepcopy(self.xWarnings)
            raise xEx
        # endtry

        if self.dicVarData.get("@top") is not None:
            del self.dicVarData["@top"]
        # endif

        self.ClearVarLocals()
        self.ClearFuncLocals()

        self.sImportPath = sSelfImportPath
        self.bIgnoreImport = sSelfIgnoreImport

        if lProcPathLists is None:
            # add collected global variables to result if
            # result is a dictionary.
            if isinstance(xResult, dict):
                data.AddVarsToData(
                    xResult,
                    dicGlobals=self.dicVarGlo,
                    dicFuncGlobals=self.dicVarFuncGlo,
                    bAllowOverwrite=True,
                    bThrowOnDisallow=False,
                    bPrintWarnings=False,
                )
            # endif

            return xResult
        else:
            return lProcPathResults
        # endif

    # enddef

    ################################################################################
    def _PreProcess(self, _xData):
        dicPre = _xData.get("__pre__")
        if dicPre is not None:
            self._EnterParseContext(EParseContext.PRE)

            # keep globals of pre-block for second pass
            xPreResult, bIsProcessed = self.InnerProcess(dicPre)

            # update data block with pre-processed block
            for sId, xPreEl in xPreResult.items():
                if (
                    sId.startswith("__")
                    and sId in _xData
                    and isinstance(_xData[sId], dict)
                    and isinstance(xPreEl, dict)
                ):
                    data.AssertDisjunctVarDicts(xPreEl, _xData[sId], "__pre__{{{0}}}".format(sId), sId)
                    _xData[sId].update(xPreEl)
                else:
                    _xData[sId] = xPreEl
                # endif
            # endfor

            # Remove preprocess block
            del _xData["__pre__"]

            self._ExitParseContext()
        # endif

    # endif

    ################################################################################
    def ApplyIncludes(self, _xData, *, _sImportPath: str, _lIncHist: Optional[list] = None):
        lIncs = _xData.get("__includes__")
        if lIncs is None:
            return
        # endif

        if not isinstance(lIncs, list):
            raise CParserError_Message(sMsg="Element type of '__includes__' must be a list")
        # endif

        lIncludeHistory = []
        if isinstance(_lIncHist, list):
            lIncludeHistory = _lIncHist.copy()
        # endif

        for sInc in lIncs:
            try:
                self._EnterParseContext(EParseContext.INC, sInc)

                sProcInc, bIsProc = self.InnerProcess(sInc)
                if not bIsProc:
                    raise CParserError_Message(sMsg="Include path could not be processed: {}".format(sInc))
                # endif

                pathInc: Path = path.MakeNormPath(sProcInc)
                if not pathInc.is_absolute():
                    pathInc = path.MakeNormPath([_sImportPath, sProcInc])
                # endif

                if pathInc.as_posix() in lIncludeHistory:
                    raise CParserError_Message(sMsg="Include file recursively included: {}".format(pathInc.as_posix()))
                # endif

                dicIncRaw = io.LoadJson(pathInc)
                if not isinstance(dicIncRaw, dict):
                    raise CParserError_Message(sMsg="Included file is not a dictionary: {}".format(pathInc.as_posix()))
                # endif
                lIncludeHistory.append(pathInc.as_posix())

                sStoreImportPath = self.sImportPath
                self.sImportPath = pathInc.parent.as_posix()
                dicInc, bIsProcessed = self.InnerProcess(dicIncRaw)
                self.sImportPath = sStoreImportPath

                data.UpdateDict(
                    _xData,
                    dicInc,
                    "includes",
                    bAllowOverwrite=False,
                    bThrowOnDisallow=False,
                )

                self._ExitParseContext()
            except Exception as xEx:
                raise CParserError_Message(sMsg="Error processing include file: {}".format(sInc), xChildEx=xEx)
            # endtry
        # endif

        # remove the includes element
        del _xData["__includes__"]

    # enddef

    ################################################################################
    def ApplyDataVariables(self, _xData):
        lKeys = self._DoApplyDataVariables(_xData)
        if self._DoApplyIncludesForDataVariables(_xData) is True:
            lAddKeys = self._DoApplyDataVariables(_xData)
            for sKey in lAddKeys:
                if sKey not in lKeys:
                    lKeys.append(sKey)
                # endif
            # endfor
        # endif

        return lKeys

    # enddef

    ################################################################################
    def _DoApplyIncludesForDataVariables(self, _xData):
        lDataVars = [
            "__eval_globals__",
            "__globals__",
            "__eval_locals__",
            "__locals__",
            "__func_globals__",
            "__func_locals__",
            "__runtime_vars__",
        ]

        bHasIncludes = False
        for sVar in lDataVars:
            dicVars = _xData.get(sVar)
            if isinstance(dicVars, dict):
                bHasIncludes = True
                self.ApplyIncludes(dicVars, _sImportPath=self.sImportPath)
            # endif
        # endfor

        return bHasIncludes

    # enddef

    ################################################################################
    def _AssertValidTagsInVarDef(self, _dicVars: dict, _sWhere: str):
        lInvalidVarTags = [
            x
            for x in _dicVars
            if x.startswith("__") and x in self.lValidSpecialTags and x not in self.lValidSpecialTagsInVars
        ]
        iInvalidCnt = len(lInvalidVarTags)

        if iInvalidCnt == 0:
            return
        # endif

        if iInvalidCnt > 1:
            sLabel = "Tags"
            sTags = "', '".join(lInvalidVarTags)
        elif iInvalidCnt == 1:
            sLabel = "Tag"
            sTags = lInvalidVarTags[0]
        # endif

        raise CParserError_Message(sMsg=f"{sLabel} '{sTags}' not allowed in {_sWhere}")

    # enddef

    ################################################################################
    def _AssertValidTags(self, _dicVars: dict, _sWhere: str):
        lInvalidSpecialTags = [x for x in _dicVars if x.startswith("__") and x not in self.lValidSpecialTags]
        iInvalidCnt = len(lInvalidSpecialTags)
        if iInvalidCnt == 0:
            return
        # endif

        if iInvalidCnt > 1:
            sLabel = "Tags"
            sTags = "', '".join(lInvalidSpecialTags)
        elif iInvalidCnt == 1:
            sLabel = "Tag"
            sTags = lInvalidSpecialTags[0]
        # endif

        raise CParserError_Message(sMsg=f"{sLabel} '{sTags}' not allowed in {_sWhere}")

    # enddef

    ################################################################################
    def _DoApplyDataVariables(self, _xData):
        lKeys = {"rtv": [], "globals": [], "locals": [], "func-glo": [], "func-loc": []}

        if "__eval_globals__" in _xData:
            print("WARNING: Element '__eval_globals__' is deprecated, use '__globals__' instead")
        # endif

        if "__eval_locals__" in _xData:
            print("WARNING: Element '__eval_locals__' is deprecated, use '__locals__' instead")
        # endif

        # test whether globals and eval globals have elements
        # with the same name
        data.AssertDisjunctVarDicts(
            _xData.get("__globals__"),
            _xData.get("__eval_globals__"),
            "__globals__",
            "__eval_globals__",
        )

        data.AssertDisjunctVarDicts(
            _xData.get("__locals__"),
            _xData.get("__eval_locals__"),
            "__locals__",
            "__eval_locals__",
        )

        ######################################################################################
        # get elements in "__runtime_vars__"
        dicRtVars = _xData.get("__runtime_vars__", {})
        if not isinstance(dicRtVars, dict):
            raise CParserError_Message(sMsg="Element '__runtime_vars__' must be a dictionary")
        # endif
        if len(dicRtVars) > 0:
            dicRtVars = data.GetPlatformDict(dicRtVars)
        # endif

        self._AssertValidTagsInVarDef(dicRtVars, "definition of '__runtime_vars__'")

        ######################################################################################
        # get elements in "__globals__" and "__eval_globals__"
        dicEvalGlob = _xData.get("__eval_globals__", {})
        if not isinstance(dicEvalGlob, dict):
            raise CParserError_Message(sMsg="Element '__eval_globals__' must be a dictionary")
        # endif
        if len(dicEvalGlob) > 0:
            dicEvalGlob = data.GetPlatformDict(dicEvalGlob)
        # endif

        dicGlob = _xData.get("__globals__", {})
        if not isinstance(dicGlob, dict):
            raise CParserError_Message(sMsg="Element '__globals__' must be a dictionary")
        # endif
        if len(dicGlob) > 0:
            dicGlob = data.GetPlatformDict(dicGlob)
        # endif

        dicGlobals = dicEvalGlob
        dicGlobals.update(dicGlob)
        del dicEvalGlob
        del dicGlob

        self._AssertValidTagsInVarDef(dicGlobals, "definition of '__globals__'")

        ######################################################################################
        # get elements in "__locals__" and "__eval_locals__"
        dicEvalLoc = _xData.get("__eval_locals__", {})
        if not isinstance(dicEvalLoc, dict):
            raise CParserError_Message(sMsg="Element '__eval_locals__' must be a dictionary")
        # endif
        if len(dicEvalLoc) > 0:
            dicEvalLoc = data.GetPlatformDict(dicEvalLoc)
        # endif

        dicLoc = _xData.get("__locals__", {})
        if not isinstance(dicLoc, dict):
            raise CParserError_Message(sMsg="Element '__locals__' must be a dictionary")
        # endif
        if len(dicLoc) > 0:
            dicLoc = data.GetPlatformDict(dicLoc)
        # endif

        dicLocals = dicEvalLoc
        dicLocals.update(dicLoc)
        del dicEvalLoc
        del dicLoc

        self._AssertValidTagsInVarDef(dicLocals, "definition of '__locals__'")

        ######################################################################################
        data.AssertDisjunctVarDicts(
            dicGlobals,
            _xData.get("__func_globals__"),
            "__globals__",
            "__func_globals__",
        )

        data.AssertDisjunctVarDicts(dicLocals, _xData.get("__func_locals__"), "__locals__", "__func_locals__")

        dicFuncLoc = _xData.get("__func_locals__", {})
        if not isinstance(dicFuncLoc, dict):
            raise CParserError_Message(sMsg="Element '__func_locals__' must be a dictionary")
        # endif
        if len(dicFuncLoc) > 0:
            dicFuncLoc = data.GetPlatformDict(dicFuncLoc)
        # endif

        self._AssertValidTagsInVarDef(dicFuncLoc, "definition of '__func_locals__'")

        dicFuncGlo = _xData.get("__func_globals__", {})
        if not isinstance(dicFuncGlo, dict):
            raise CParserError_Message(sMsg="Element '__func_globals__' must be a dictionary")
        # endif
        if len(dicFuncGlo) > 0:
            dicFuncGlo = data.GetPlatformDict(dicFuncGlo)
        # endif

        self._AssertValidTagsInVarDef(dicFuncGlo, "definition of '__func_globals__'")

        ######################################################################################
        # add func globals to var dict
        if len(dicFuncGlo) > 0:
            data.UpdateDict(
                self.dicVarFuncGlo,
                dicFuncGlo,
                "function globals",
                bAllowOverwrite=True,
                bPrintWarnings=False,
                bIgnoreSpecialVars=True,
            )
            lKeys["func-glo"].extend(dicFuncGlo.keys())
        # endif

        ######################################################################################
        # add func locals to var dict
        if len(dicFuncLoc) > 0:
            data.UpdateDict(
                self.dicVarFuncLoc,
                dicFuncLoc,
                "function locals",
                bAllowOverwrite=True,
                bPrintWarnings=False,
                bIgnoreSpecialVars=True,
            )
            lKeys["func-loc"].extend(dicFuncLoc.keys())
        # endif

        ######################################################################################
        # add globals to var dict
        if len(dicGlobals) > 0:
            data.UpdateDict(
                self.dicVarGlo,
                dicGlobals,
                "globals",
                bAllowOverwrite=True,
                bPrintWarnings=False,
                bIgnoreSpecialVars=True,
            )
            lKeys["globals"].extend(dicGlobals.keys())
            # Newly added globals are removed from evaluated set
            for sKey in dicGlobals:
                if sKey in self.setVarGloEval:
                    self.setVarGloEval.remove(sKey)
                # endif
            # endfor
        # endif

        ######################################################################################
        # add locals to var dict
        if len(dicLocals) > 0:
            data.UpdateDict(
                self.dicVarLoc,
                dicLocals,
                "locals",
                bAllowOverwrite=True,
                bPrintWarnings=False,
                bIgnoreSpecialVars=True,
            )
            lKeys["locals"].extend(dicLocals.keys())
            # Newly added locals are removed from evaluated set
            for sKey in dicLocals:
                if sKey in self.setVarLocEval:
                    self.setVarLocEval.remove(sKey)
                # endif
            # endfor
        # endif

        ######################################################################################
        # add runtime vars to var dict
        if len(dicRtVars) > 0:
            data.UpdateDict(
                self.dicVarRtv,
                dicRtVars,
                "runtime vars",
                bAllowOverwrite=True,
                bPrintWarnings=False,
                bIgnoreSpecialVars=True,
            )
            lKeys["rtv"].extend(dicRtVars.keys())
            # Newly added locals are removed from evaluated set
            for sKey in dicRtVars:
                if sKey in self.setVarRtvEval:
                    self.setVarRtvEval.remove(sKey)
                # endif
            # endfor
        # endif

        ######################################################################################
        # Evaluate locals
        if len(dicLocals) > 0:
            try:
                self._EnterParseContext(EParseContext.LOC)
                for sVarKey in dicLocals:
                    if sVarKey.startswith("__"):
                        continue
                    # endif
                    try:
                        self._EnterParseContext(EParseContext.VAR, sVarKey)
                        xEval, bIsProc = self.InnerProcess(self.dicVarLoc[sVarKey])
                    except Exception as xEx:
                        raise CParserError_Message(sMsg=f"Error parsing variable '{sVarKey}'", xChildEx=xEx)
                    finally:
                        self._ExitParseContext()
                    # endtry

                    if bIsProc is True:
                        self.setVarLocEval.add(sVarKey)
                        self.dicVarLoc[sVarKey] = xEval
                        dicLocals[sVarKey] = xEval
                    # endif
                # endfor
            except Exception as xEx:
                raise CParserError_Message(sMsg="Error parsing '__locals__'", xChildEx=xEx)
            finally:
                self._ExitParseContext()
            # endtry

            _xData["__locals__"] = dicLocals
        # endif

        ######################################################################################
        # Evaluate globals
        if len(dicGlobals) > 0:
            try:
                self._EnterParseContext(EParseContext.GLO)
                for sVarKey in dicGlobals:
                    if sVarKey.startswith("__"):
                        continue
                    # endif
                    try:
                        self._EnterParseContext(EParseContext.VAR, sVarKey)
                        xEval, bIsProc = self.InnerProcess(self.dicVarGlo[sVarKey])
                    except Exception as xEx:
                        raise CParserError_Message(sMsg=f"Error parsing variable '{sVarKey}'", xChildEx=xEx)
                    finally:
                        self._ExitParseContext()
                    # endtry
                    if bIsProc is True:
                        self.setVarGloEval.add(sVarKey)
                        self.dicVarGlo[sVarKey] = xEval
                        dicGlobals[sVarKey] = xEval
                    # endif
                # endfor

                _xData["__globals__"] = dicGlobals
            except Exception as xEx:
                raise CParserError_Message(sMsg="Error parsing '__globals__'", xChildEx=xEx)
            finally:
                self._ExitParseContext()
            # endtry
        # endif

        ######################################################################################
        # Evaluate runtime vars
        if len(dicRtVars) > 0:
            try:
                self._EnterParseContext(EParseContext.RTV)
                for sVarKey in dicRtVars:
                    if sVarKey.startswith("__"):
                        continue
                    # endif
                    if sVarKey.startswith("@"):
                        raise CParserError_Message(sMsg=f"Runtime variable name must not start with '@': '{sVarKey}'")
                    # endif

                    try:
                        self._EnterParseContext(EParseContext.VAR, sVarKey)
                        xEval, bIsProc = self.InnerProcess(dicRtVars[sVarKey])
                    except Exception as xEx:
                        raise CParserError_Message(sMsg=f"Error parsing variable '{sVarKey}'", xChildEx=xEx)
                    finally:
                        self._ExitParseContext()
                    # endtry

                    if bIsProc is True:
                        self.setVarRtvEval.add(sVarKey)
                        self.dicVarRtv[sVarKey] = xEval
                    # endif
                # endfor

                del _xData["__runtime_vars__"]
            except Exception as xEx:
                raise CParserError_Message(sMsg="Error parsing '__runtime_vars__'", xChildEx=xEx)
            finally:
                self._ExitParseContext()
            # endtry

        # endif

        return lKeys

    # enddef

    ################################################################################
    def InnerProcess(self, _xData, bRemoveGlobals=False, lPath=None):
        # Provide variable dictionaries if they are not defined
        self.ProvideVariables()

        bIsProcessed = True

        if isinstance(_xData, dict):
            # Load includes if any
            self.ApplyIncludes(_xData, _sImportPath=self.sImportPath)

            # Store current locals to recover them after processing
            # dicParentLocals = copy.deepcopy(self.dicVarLoc)
            # setParentLocalsEval = copy.deepcopy(self.setVarLocEval)
            # dicParentFuncLocals = copy.deepcopy(self.dicVarFuncLoc)
            self.lVarLocStack.append(self.dicVarLoc)
            self.dicVarData["@loc"] = {}

            self.lVarLocEvalStack.append(self.setVarLocEval)
            self.dicVarData["@loc-eval"] = set()

            self.lVarFuncLocStack.append(self.dicVarFuncLoc)
            self.dicVarData["@func-loc"] = {}

            lVarKeys = self.ApplyDataVariables(_xData)

            if lPath is not None and len(lPath) == 0:
                xResult = _xData
            else:
                xResult, bIsProcessed = self._ProcessDict(_xData, lPath=lPath)
            # endif

            if bRemoveGlobals:
                for sKey in lVarKeys["globals"]:
                    del self.dicVarGlo[sKey]
                # endfor

                for sKey in lVarKeys["func-glo"]:
                    del self.dicVarFuncGlo[sKey]
                # endfor
            # endif

            self.dicVarData["@loc"] = self.lVarLocStack.pop()
            self.dicVarData["@loc-eval"] = self.lVarLocEvalStack.pop()
            self.dicVarData["@func-loc"] = self.lVarFuncLocStack.pop()

        elif isinstance(_xData, list):
            if lPath is not None and len(lPath) > 0:
                raise CParserError_Message(
                    sMsg="Given process path cannot be fully traversed. Remaining path: {0}".format("/".join(lPath))
                )
            # endif
            xResult, bIsProcessed = self._ProcessList(_xData)

        elif isinstance(_xData, str):
            # Process string should process the string until
            # there are no processable variables left, or the
            # result is something else but a string.
            try:
                xResult, iMatchCnt, iProcCnt, iLiteralCnt = self._ProcessString(_xData)
                bIsProcessed = iProcCnt == iMatchCnt

                if (
                    lPath is not None
                    and len(lPath) > 0
                    and not (isinstance(xResult, dict) or isinstance(xResult, list))
                ):
                    raise CParserError_Message(
                        sMsg="Given process path cannot be fully traversed. Remaining path: {0}".format("/".join(lPath))
                    )
                # endif

                # if the result is not string, or it is a fully processed string
                # then process the result again
                if (not isinstance(xResult, str) or iMatchCnt > iLiteralCnt) and bIsProcessed:
                    xResult, bIsProc = self.InnerProcess(xResult, lPath=lPath)
                    bIsProcessed = bIsProcessed and bIsProc
                # endif
            except Exception as xEx:
                raise CParserError_ProcStr(sString=_xData, xChildEx=xEx)
            # endtry
        else:
            xResult = _xData
        # endif

        return xResult, bIsProcessed

    # enddef

    ################################################################################
    # Process a dictionary
    def _ProcessDict(self, _dicData, *, lPath=None):
        # The output processed dictionary
        dicResult = {}
        bIsProcessed = True

        dicActData = data.GetPlatformDict(_dicData)

        self._EnterParseContext(EParseContext.DICT)
        self._AssertValidTags(dicActData, "dictionary")

        if "__lambda__" in dicActData:
            # This is a "lambda function"
            dicLambda = copy.deepcopy(dicActData)
            del dicLambda["__lambda__"]
            sLambda = lambda_parser.ToLambdaString(dicLambda)
            dicResult = "$L{{$*{{^{0}}}}}".format(sLambda)
            bIsProcessed = True

        elif lPath is None or lPath[0] == "*":
            # Loop over all elements of the input dictionary
            for sObjId, xData in dicActData.items():
                try:
                    bIsProc = self._ProcessDictItem(dicResult, sObjId, xData)
                    bIsProcessed = bIsProcessed and bIsProc
                except Exception as xEx:
                    raise CParserError_DictSel(dicData=dicActData, xId=sObjId, xChildEx=xEx)
                # endtry
            # endfor

        elif len(lPath) > 0:
            sObjId = lPath[0]
            lSubPath = lPath[1:]
            if sObjId not in dicActData:
                # raise Exception("Path component '{0}' not found in data".format(sObjId))
                dicResult = None
            else:
                try:
                    xData = dicActData[sObjId]
                    bIsProc = self._ProcessDictItem(dicResult, sObjId, xData, lPath=lSubPath)
                    bIsProcessed = bIsProcessed and bIsProc
                except Exception as xEx:
                    raise CParserError_DictSel(dicData=dicActData, xId=sObjId, xChildEx=xEx)
                # endtry
            # endif

        else:
            dicResult = dicActData

        # endif

        self._ExitParseContext()

        return dicResult, bIsProcessed

    # enddef

    ################################################################################
    def _ProcessDictItem(self, _dicResult, _sObjId, _xData, lPath=None):
        # if the object id is a special key word, ignore the content
        # for example, locals, globals and pre elements are not processed here
        if _sObjId.startswith("__"):
            _dicResult[_sObjId] = _xData
            return True
        # endif

        self._EnterParseContext(EParseContext.DICT_EL, _sObjId)

        bIsProcessed = True

        # Check whether the current dictionary key contains a variable
        try:
            lMatch = text.GetVarMatchList(_sObjId, self.reVarStart)
        except Exception as xEx:
            raise CParserError_ProcKey(sType="proc-key", sKey=_sObjId, xChildEx=xEx)
        # endtry

        iVarCnt = len(lMatch)

        if iVarCnt == 0:
            # The key does not contain a variable.
            # In this case, process the key's content and store the result in the output dict.
            _dicResult[_sObjId], bIsProc = self.InnerProcess(_xData, lPath=lPath)
            bIsProcessed = bIsProcessed and bIsProc

        elif iVarCnt > 1:
            # Process all matches
            # Expect that all matches are strings. Otherwise, this is an error.
            sNewObjId = ""
            iStart = 0
            iLiteralCnt = 0
            for dicMatch in lMatch:
                try:
                    xVarData, bIsLiteral = self._ProcessVarMatch(dicMatch)
                except Exception as xEx:
                    raise CParserError_KeyStrMatch(sString=_sObjId, dicMatch=dicMatch, xChildEx=xEx)
                # endtry

                if xVarData is not None and (isinstance(xVarData, list) or isinstance(xVarData, dict)):
                    raise CParserError_Message(
                        sMsg="If a variable in a dictionary key results in a list or dictionary, "
                        "it has to be the only variable. See key: {0}".format(_sObjId)
                    )
                # endif

                iLiteralCnt += 1 if bIsLiteral is True else 0

                sNewObjId += _sObjId[iStart : dicMatch.get("iStart")]
                if xVarData is not None:
                    sNewObjId += str(xVarData)
                else:
                    sNewObjId += _sObjId[dicMatch.get("iStart") : dicMatch.get("iEnd")]
                    bIsProcessed = False
                # endif
                iStart = dicMatch.get("iEnd")
            # endfor
            sNewObjId += _sObjId[iStart:]

            if bIsProcessed is True and iLiteralCnt == 0:
                try:
                    bIsProc = self._ProcessDictItem(_dicResult, sNewObjId, _xData, lPath=lPath)
                    bIsProcessed = bIsProcessed and bIsProc
                except Exception as xEx:
                    raise CParserError_DictSel(dicData=_xData, xId=sNewObjId, xChildEx=xEx)
                # endtry
            # endif

        elif iVarCnt == 1:
            # Process the match
            dicMatch = lMatch[0]
            try:
                xVarData, bIsLiteral = self._ProcessVarMatch(dicMatch)
            except Exception as xEx:
                raise CParserError_KeyStrMatch(sString=_sObjId, dicMatch=dicMatch, xChildEx=xEx)
            # endtry

            # print(f"Parse key in dict: {_sObjId}")
            # print(f"  xVarData: {xVarData}")

            # If the variable is not in the replacement dictionary...
            if xVarData is None or bIsLiteral is True:
                # ... then process the key's content and leave the key unchanged, as it may be processed later.
                _dicResult[_sObjId], bIsProc = self.InnerProcess(_xData, lPath=lPath)
                bIsProcessed = bIsProcessed and bIsProc

            else:
                # If the variable is in the replacement dictionary, then...
                if isinstance(xVarData, str):
                    # if it is a string, use this string a new key and process the content
                    sNewObjId = _sObjId[0 : dicMatch.get("iStart")] + xVarData + _sObjId[dicMatch.get("iEnd") :]
                    try:
                        bIsProc = self._ProcessDictItem(_dicResult, sNewObjId, _xData, lPath=lPath)
                        bIsProcessed = bIsProcessed and bIsProc
                    except Exception as xEx:
                        raise CParserError_DictItem(xData=_xData, xId=sNewObjId, xChildEx=xEx)
                    # endtry

                elif isinstance(xVarData, list):
                    # if the variable content is a list, then loop over the list
                    for iVarIdx, xVar in enumerate(xVarData):
                        # if the variable is a string, then use it as new key
                        if isinstance(xVar, str):
                            sNewObjId = xVar

                        elif isinstance(xVar, dict):
                            sNewObjId = str(iVarIdx)

                        else:
                            raise CParserError_Message(
                                sMsg="Invalid variable value type in list for variable '{0}':\n"
                                "{1}".format(dicMatch.get("sMatch"), str(xVar))
                            )
                        # endif

                        sNewObjId = _sObjId[0 : dicMatch.get("iStart")] + sNewObjId + _sObjId[dicMatch.get("iEnd") :]

                        sCtxId = sCtxIdBase = "@ctx"
                        sCtxKeyId = sCtxKeyIdBase = "@key"
                        sCtxValId = sCtxValIdBase = "@value"
                        iCtxIdx = 0
                        while sCtxId in self.dicVarData:
                            iCtxIdx += 1
                            sCtxId = "{0}-{1}".format(sCtxIdBase, iCtxIdx)
                        # endwhile

                        if iCtxIdx > 0:
                            sCtxKeyId = "{0}-{1}".format(sCtxKeyIdBase, iCtxIdx)
                            sCtxValId = "{0}-{1}".format(sCtxValIdBase, iCtxIdx)
                        # endif

                        self.dicVarData[sCtxId] = xVarData
                        self.dicVarData[sCtxKeyId] = str(iVarIdx)
                        self.dicVarData[sCtxValId] = xVar

                        try:
                            bIsProc = self._ProcessDictItem(_dicResult, sNewObjId, _xData, lPath=lPath)
                            bIsProcessed = bIsProcessed and bIsProc
                        except Exception as xEx:
                            raise CParserError_DictItem(xData=_xData, xId=sNewObjId, xChildEx=xEx)
                        # endtry

                        del self.dicVarData[sCtxId]
                        del self.dicVarData[sCtxKeyId]
                        del self.dicVarData[sCtxValId]
                    # endfor

                elif isinstance(xVarData, dict):
                    # Use keys of dictionary as new object ids and the elements
                    # as data in the variable data for the current match.
                    for sKey, xEl in xVarData.items():
                        sNewObjId = _sObjId[0 : dicMatch.get("iStart")] + sKey + _sObjId[dicMatch.get("iEnd") :]

                        # sCtxId = sCtxIdBase = "@context"
                        # iCtxIdx = 1
                        # while sCtxId in self.dicVarData:
                        #     sCtxId = "{0}{1}".format(sCtxIdBase, iCtxIdx)
                        #     iCtxIdx += 1
                        # # endwhile

                        sCtxId = sCtxIdBase = "@ctx"
                        sCtxKeyId = sCtxKeyIdBase = "@key"
                        sCtxValId = sCtxValIdBase = "@value"
                        iCtxIdx = 0
                        while sCtxId in self.dicVarData:
                            iCtxIdx += 1
                            sCtxId = "{0}-{1}".format(sCtxIdBase, iCtxIdx)
                        # endwhile

                        if iCtxIdx > 0:
                            sCtxKeyId = "{0}-{1}".format(sCtxKeyIdBase, iCtxIdx)
                            sCtxValId = "{0}-{1}".format(sCtxValIdBase, iCtxIdx)
                        # endif

                        self.dicVarData[sCtxId] = xVarData
                        self.dicVarData[sCtxKeyId] = sKey
                        self.dicVarData[sCtxValId] = xEl

                        try:
                            bIsProc = self._ProcessDictItem(_dicResult, sNewObjId, _xData, lPath=lPath)
                            bIsProcessed = bIsProcessed and bIsProc

                        except Exception as xEx:
                            raise CParserError_DictItem(xData=_xData, xId=sNewObjId, xChildEx=xEx)
                        # endtry

                        del self.dicVarData[sCtxId]
                        del self.dicVarData[sCtxKeyId]
                        del self.dicVarData[sCtxValId]
                    # endfor
                # endif
            # endif
        # endif

        self._ExitParseContext()

        return bIsProcessed

    # enddef

    ################################################################################
    def _ProcessList(self, _lData):
        lResult = []
        bIsProcessed = True

        self._EnterParseContext(EParseContext.LIST)

        if len(_lData) > 0 and _lData[0] == "__lambda__":
            # This is a "lambda function"
            lLambda = copy.deepcopy(_lData)
            lLambda.pop(0)
            sLambda = lambda_parser.ToLambdaString(lLambda)
            lResult = "$L{{$*{{^{0}}}}}".format(sLambda)
            bIsProcessed = True

        else:
            for iIdx, xObj in enumerate(_lData):
                try:
                    self._EnterParseContext(EParseContext.LIST_EL, str(iIdx))

                    xResult, bIsProc = self.InnerProcess(xObj)
                    lResult.append(xResult)
                    bIsProcessed = bIsProcessed and bIsProc

                    self._ExitParseContext()
                except Exception as xEx:
                    raise CParserError_ListSel(iIdx=iIdx, lData=_lData, xChildEx=xEx)
                # endtry
            # endfor
        # endif

        self._ExitParseContext()

        return lResult, bIsProcessed

    # enddef

    ################################################################################
    # Check whether string contains a variable ${[...]}
    def _HasVar(self, _sValue):
        if not isinstance(_sValue, str):
            return False
        # endif

        xMatch = self.reVarStart.search(_sValue, 0)
        return xMatch is not None

    # enddef

    ################################################################################
    def _ProcessString(self, _sData):
        # Find all variable matches
        try:
            lMatch = text.GetVarMatchList(_sData, self.reVarStart)
        except Exception as xEx:
            raise CParserError_ProcStr(sString=_sData, sContext="Find variables", xChildEx=xEx)
        # endtry
        iMatchCnt = len(lMatch)

        sR = ""
        iStart = 0
        iProcCnt = 0
        iLiteralCnt = 0
        for dicMatch in lMatch:
            # Process the match
            try:
                xValue, bIsLiteral = self._ProcessVarMatch(dicMatch)
            except Exception as xEx:
                raise CParserError_StrMatch(sString=_sData, dicMatch=dicMatch, xChildEx=xEx)
            # endtry

            # if bLiteral == True, the result should not be processed further.
            # For example, the lambda function scope $L{} or definition $L*{},
            # return an object that should not be processed further but taken
            # literally.
            bIsProc = False

            if xValue is not None:
                bIsProc = True

                if bIsLiteral is False:
                    # if the result is a string again, process this string, until
                    # there are no more matches or the result is not a string anymore.
                    # If a variable cannot be found, None is returned, which also ends
                    # the loop.
                    while isinstance(xValue, str):
                        try:
                            (
                                xValue,
                                iValMatchCnt,
                                iValProcCnt,
                                iValLiteralCnt,
                            ) = self._ProcessString(xValue)
                        except Exception as xEx:
                            raise CParserError_ProcStr(
                                sString=xValue,
                                sContext="Recurse string processing",
                                xChildEx=xEx,
                            )
                        # endtry

                        # iMatchCnt += iValMatchCnt
                        # iProcCnt += iValProcCnt
                        # iLiteralCnt += iValLiteralCnt

                        # Total number of non-literal matches
                        iValNonLitMatchCnt = iValMatchCnt - iValLiteralCnt

                        if iValNonLitMatchCnt == 0 or iValProcCnt < iValMatchCnt or xValue is None:
                            bIsProc = iValProcCnt == iValMatchCnt
                            bIsLiteral = iValLiteralCnt > 0
                            break
                        # endif

                        # # break loop if no variable could be processed in xValue
                        # # or no variable exists.
                        # if iValProcCnt == 0:
                        #     break
                        # # endif
                    # endwhile xValue is string

                # endif not bIsLiteral
            # endif xValue is not None

            iProcCnt += 1 if bIsProc is True else 0
            iLiteralCnt += 1 if bIsLiteral is True else 0

            sFront = _sData[0 : dicMatch["iStart"]].strip()
            sBack = _sData[dicMatch["iEnd"] :].strip()

            # bIsSingleVar = (dicMatch.get("iStart") == 0 and dicMatch.get("iEnd") == len(_sData))
            bIsSingleVar = len(sFront) == 0 and len(sBack) == 0

            if xValue is None:
                continue
            # endif

            if bIsSingleVar and not isinstance(xValue, str):
                return xValue, iMatchCnt, iProcCnt, iLiteralCnt
            # endif

            if not isinstance(xValue, str):
                xValue = text.ToString(xValue)
                # raise Exception("Result of variable '{0}' is not a string".format(_sData))
            # endif

            sR += _sData[iStart : dicMatch.get("iStart")] + xValue
            iStart = dicMatch.get("iEnd")
        # endfor

        sR += _sData[iStart:]

        if iLiteralCnt == 0 and iMatchCnt == iProcCnt:
            sR = text.StripString(sR, "`")
        # endif

        return sR, iMatchCnt, iProcCnt, iLiteralCnt

    # enddef

    ################################################################################
    def _ProcessArgs(self, _lArgs):
        lVarIsProc = []
        lVarData = []

        for iArgIdx, sArg in enumerate(_lArgs):
            self._EnterParseContext(EParseContext.ARG, sArg)
            # dummy loop to enable break to jump to end of while
            while True:
                xMatch = reLambdaPar.match(sArg)
                if xMatch is not None:
                    lVarData.append(sArg)
                    lVarIsProc.append(False)
                    break
                # endif

                xMatch = reLiteralArg.match(sArg)
                if xMatch is not None:
                    sArg = sArg.strip()

                    lVarData.append(sArg[1:])
                    lVarIsProc.append(True)
                    break
                # endif literal arg

                # unroll result of argument function as new argument list
                # If an argument is given as "*${value}", then
                # "${value}" is processed and the result is unwrapped
                # as a list of arguments, that is inserted at the position
                # of the original argument.
                xMatch = reUnrollArg.match(sArg)
                if xMatch is not None:
                    sArg = sArg.strip()
                    try:
                        lSubVarData, lSubVarIsProc = self._ProcessArgs([sArg[1:]])
                    except Exception as xEx:
                        raise CParserError_ProcArgStr(
                            sString=sArg[1:],
                            sContext="Unroll result of argument string",
                            xChildEx=xEx,
                        )
                    # endtry

                    if lSubVarIsProc[0] is False:
                        return None, None
                    else:
                        xSubVarData = lSubVarData[0]
                        if isinstance(xSubVarData, list):
                            lVarData.extend(xSubVarData)
                        elif isinstance(xSubVarData, dict):
                            lVarData.extend(list(xSubVarData.items()))
                        else:
                            lVarData.append(xSubVarData)
                        # endif

                        lVarIsProc.append(lSubVarIsProc[0])
                    # endif
                    break
                # endif unroll arg

                xMatch = reNamedArg.match(sArg)
                if xMatch is not None:
                    sKey = xMatch.group("name")
                    sValue = xMatch.group("value")

                    xMatchUnrollArg = reUnrollArg.match(sValue)
                    xMatchTupleArg = reTupleArg.match(sValue)

                    lSubVarData, lSubVarIsProc = self._ProcessArgs([sValue])

                    if xMatchTupleArg is not None:
                        lVarData.append(var_nt.Create(sKey, lSubVarData[0]))

                    elif xMatchUnrollArg is not None or len(lSubVarData) > 1:
                        lVarData.append(var_nt.Create(sKey, tuple(lSubVarData)))

                    else:
                        lVarData.append(var_nt.Create(sKey, lSubVarData[0]))
                    # endif
                    lVarIsProc.append(all(lSubVarIsProc))
                    break
                # endif

                xMatch = reTupleArg.match(sArg)
                if xMatch is not None:
                    sArg = sArg.strip()
                    # if the argument starts with '(' then process the element
                    # inside the bracket and put the result into a tuple and
                    # this tuple into the returned argument list.
                    # Functions receive this tuple as a single argument and can
                    # do specific processing. For example, the lambda foreach
                    # processes the lambda function for each tuple, using the elements
                    # of the tuple as lambda parameters.
                    iClosedIdx = text.FindBalancedChar(sArg, 0, ")")
                    if iClosedIdx == len(sArg) - 1:
                        try:
                            lSubArgs, lSubEndIdx = text.SplitArgs(sArg[1:-1])
                            lSubVarData, lSubVarIsProc = self._ProcessArgs(lSubArgs)
                        except Exception as xEx:
                            raise CParserError_ProcArgStr(
                                sString=sArg,
                                sContext="Process tuple argument",
                                xChildEx=xEx,
                            )
                        # endtry
                        lVarData.append(tuple(lSubArgs))
                        lVarIsProc.append(all(lSubVarIsProc))
                    # endif
                    break
                # endif tuple arg

                bIsProcessed = False

                try:
                    xVarData, bIsProcessed = self.InnerProcess(sArg)
                except Exception as xEx:
                    raise CParserError_ProcArgListElement(lArgList=_lArgs, iArgIdx=iArgIdx, xChildEx=xEx)
                # endtry

                lVarData.append(xVarData)
                lVarIsProc.append(bIsProcessed)
                break
            # endwhile dummy loop
            self._ExitParseContext()
        # endfor

        return lVarData, lVarIsProc

    # enddef

    ################################################################################
    def _ProcessVarMatch(self, _dicMatch):
        if _dicMatch is None:
            return None
        # endif

        sFunc = _dicMatch.get("sFunc")
        lArgs = _dicMatch.get("lArgs")

        self._EnterParseContext(EParseContext.FUNC, sFunc, lArgs)

        lVarIsProc = []

        if sFunc in self.lLiteralArgsFuncs:
            lVarData = lArgs
            lVarIsProc = [False for x in lArgs]
        else:
            try:
                lVarData, lVarIsProc = self._ProcessArgs(lArgs)
            except Exception as xEx:
                raise CParserError_ProcFuncArgs(sFunc=sFunc, lArgs=lArgs, xChildEx=xEx)
            # endtry
            if lVarData is None:
                return None, False
            # endif
        # endif

        try:
            xResult, bIsLiteral = self._ProcessFunc(sFunc, lVarData, lVarIsProc)
        except Exception as xEx:
            raise CParserError_ProcFunc(sFunc=sFunc, lArgs=lVarData, xChildEx=xEx)
        # endtry

        self._ExitParseContext()
        return xResult, bIsLiteral

    # enddef

    ################################################################################
    def ExecFunc(self, _sFunc, *_tArgs):
        lArgs = list(_tArgs)
        lArgIsProc = [True for x in lArgs]
        xResult, bIsLiteral = self._ProcessFunc(_sFunc, lArgs, lArgIsProc)

        return xResult, bIsLiteral

    # enddef

    ################################################################################
    def _ProcessFunc(self, _sFunc, _lArgs, _lArgIsProc):
        funcExec = self.dicFunc.get(_sFunc)
        if funcExec is None:
            lParts = _sFunc.split(".")
            sFuncGrp = "{}.*".format(lParts[0])
            funcExec = self.dicFunc.get(sFuncGrp)
            if funcExec is None:
                raise CParserError_Message(sMsg="Function '{0}' not available".format(_sFunc))
            # endif
            xResult, bIsLiteral = funcExec(self, _lArgs, _lArgIsProc, sFuncName=_sFunc, lFuncParts=lParts)

        else:
            xResult, bIsLiteral = funcExec(self, _lArgs, _lArgIsProc, sFuncName=_sFunc)

        # endif

        return xResult, bIsLiteral

    # enddef

    ################################################################################
    def _ProcVar(self, _dicVarRead: dict, _setVarEvalRead: set, _sKey: str, _dicVarWrite: dict, _setVarEvalWrite: set):
        bFound = False
        bIsProc = False
        xNewVal = None

        if _sKey in _setVarEvalRead:
            bFound = True
            bIsProc = True
            xNewVal = _dicVarRead[_sKey]

        elif _sKey in _dicVarRead and not _sKey.startswith("__"):
            self._EnterParseContext(EParseContext.VAR, _sKey)
            bFound = True
            xVar = _dicVarRead[_sKey]
            xNewVal, bIsProc = self.InnerProcess(xVar)
            # if the variable is not fully processed, then do not flag it as processed,
            # but store the possibly partially processed result back in the variable dict.
            if bIsProc is True:
                _setVarEvalWrite.add(_sKey)
            # endif
            _dicVarWrite[_sKey] = xNewVal
            self._ExitParseContext()
        # endif

        return xNewVal, bFound, bIsProc

    # enddef

    ################################################################################
    def _GetVar(self, _xData: dict, _sKey: str):
        bFound = False
        bIsProc = False
        bHasVars = False
        xNewVal = None

        if "@loc" in _xData:
            bHasVars = True
            dicLocAct: dict = _xData["@loc"]
            setLocEvalAct: set = _xData["@loc-eval"]
            xNewVal, bFound, bIsProc = self._ProcVar(dicLocAct, setLocEvalAct, _sKey, dicLocAct, setLocEvalAct)

            if bFound is False:
                lLocVarStack: list[dict] = _xData.get("@loc-s")
                lLocVarEvalStack: list[set] = _xData.get("@loc-eval-s")
                if lLocVarStack is not None and lLocVarEvalStack is not None:
                    for dicLoc, setEval in zip(reversed(lLocVarStack), reversed(lLocVarEvalStack)):
                        xNewVal, bFound, bIsProc = self._ProcVar(dicLoc, setEval, _sKey, dicLocAct, setLocEvalAct)
                        if bFound is True:
                            break
                        # endif
                    # endwhile
                # endif
            # endif
        # endif

        if bFound is False and "@glo" in _xData:
            bHasVars = True
            xNewVal, bFound, bIsProc = self._ProcVar(
                _xData["@glo"], _xData["@glo-eval"], _sKey, _xData["@glo"], _xData["@glo-eval"]
            )
        # endif

        if bFound is False and "@rtv" in _xData:
            bHasVars = True
            xNewVal, bFound, bIsProc = self._ProcVar(
                _xData["@rtv"], _xData["@rtv-eval"], _sKey, _xData["@rtv"], _xData["@rtv-eval"]
            )
        # endif

        if bFound is False and "@func-loc" in _xData:
            bHasVars = True
            if _sKey in _xData["@func-loc"]:
                bFound = True
                bIsProc = True
                xNewVal = _xData["@func-loc"][_sKey]
            # endif
            if bFound is False:
                lFuncLocVarStack: list[dict] = _xData["@func-loc-s"]
                for dicFuncLoc in reversed(lFuncLocVarStack):
                    if _sKey in dicFuncLoc:
                        bFound = True
                        bIsProc = True
                        xNewVal = dicFuncLoc[_sKey]
                        break
                    # endif
                # endfor
            # endif
        # endif

        if bFound is False and "@func-glo" in _xData:
            bHasVars = True
            if _sKey in _xData["@func-glo"]:
                bFound = True
                bIsProc = True
                xNewVal = _xData["@func-glo"][_sKey]
            # endif
        # endif

        return xNewVal, bFound, bIsProc

    # enddef

    ################################################################################
    def ProcessRefPath(self, _xValue, _lMatch: list, _iMatchIdx: int):
        if _xValue is None:
            return None, False
        # endif

        if len(_lMatch) == _iMatchIdx:
            return _xValue, False

        elif len(_lMatch) == _iMatchIdx + 1 and isinstance(_lMatch[_iMatchIdx], str) and len(_lMatch[_iMatchIdx]) == 0:
            # if this is the last element in the path and that key is an empty string,
            # then return the string result as literal.
            return _xValue, True
        # endif

        bLiteral = False
        xResult = None

        if isinstance(_xValue, str):
            xResult = _xValue

            sValue = xResult
            try:
                xResult, iMatchCnt, iProcCnt, iLiteralCnt = self._ProcessString(sValue)

            except Exception as xEx:
                raise CParserError_ProcStr(sString=sValue, sContext="Reference path", xChildEx=xEx)
            # endtry

            if xResult is None:
                raise CParserError_Message(
                    sMsg="String result '{0}' could not be fully resolved in path: {1}".format(
                        sValue, text.HighlightElementString(_lMatch, _iMatchIdx, ":")
                    )
                )
            # endif

            if isinstance(xResult, str):
                raise CParserError_Message(
                    sMsg="String result '{0}' cannot have further specialization '{1}': {2}".format(
                        xResult,
                        _lMatch[_iMatchIdx],
                        text.HighlightElementString(_lMatch, _iMatchIdx, ":"),
                    )
                )
            else:
                try:
                    xResult, bLiteral = self.ProcessRefPath(xResult, _lMatch, _iMatchIdx)
                except Exception as xEx:
                    raise CParserError_ProcRefPath(
                        sContext=f"processed string '{sValue}'",
                        lMatch=_lMatch[_iMatchIdx:],
                        iMatchIdx=0,
                        xChildEx=xEx,
                    )
                # endtry
            # endif xResult is string

        elif isinstance(_xValue, list):
            xKey = _lMatch[_iMatchIdx]
            xResult, bLiteral = self._ProcessRefPathListKey(_xValue, xKey, _lMatch, _iMatchIdx)

        elif isinstance(_xValue, dict):
            while True:
                sKey = _lMatch[_iMatchIdx]
                try:
                    lPath = text.SplitVarPath(sKey)
                except Exception as xEx:
                    raise CParserError_ProcKey(sKey=sKey, xChildEx=xEx)
                # endtry

                if len(lPath) <= 1:
                    break
                # endif
                _lNewMatch = _lMatch[0:_iMatchIdx]
                _lNewMatch.extend(lPath)
                _lNewMatch.extend(_lMatch[_iMatchIdx + 1 :])
                _lMatch = _lNewMatch
            # endwhile

            if sKey.startswith("__"):
                raise CParserError_Message(sMsg=f"Keys starting with '__' are not allowed: '{sKey}'")
            # endif

            # Try to obtain variable from global, locals, func vars
            xNewVal, bFound, bIsProc = self._GetVar(_xValue, sKey)
            if bFound is True and (xNewVal is None or bIsProc is False):
                # Variable was found but could not be fully evaluated.
                self._bIsFullyProcessed = False
                return None, False

            elif bFound is False:
                xNewVal = _xValue.get(sKey)

                if xNewVal is None:
                    self.AddWarning(EWarningType.UNDEF_VAR, sKey)
                # endif
            # endif

            if xNewVal is None:
                if _iMatchIdx + 1 == len(_lMatch) and len(sKey) == 0:
                    xResult = _xValue
                    bLiteral = True

                elif _iMatchIdx == 0:
                    # the top level path element is not found in current dictionary.
                    # In this case, return None to indicate that the path cannot be found currently.
                    xResult = None
                    bLiteral = True
                    self._bIsFullyProcessed = False

                else:
                    # lKeyVal: list[str] = [f"{k}: {v}" for k, v in _xValue.items()]
                    # raise CParserError_Message(
                    #     sMsg="Key '{0}' not found in dictionary. Available keys are: {1}\n".format(
                    #         sKey, CParserError.ListToString(lKeyVal)
                    #     )
                    # )
                    if bFound is False:
                        raise CParserError_Message(
                            sMsg="Key '{0}' not found in dictionary. Available keys are: {1}\n".format(
                                sKey, CParserError.ListToString(list(_xValue.keys()))
                            )
                        )
                    else:
                        raise CParserError_Message(sMsg=f"Key '{sKey}' found in dictionary but value is undefined.")
                # endif
            else:
                try:
                    xResult, bLiteral = self.ProcessRefPath(xNewVal, _lMatch, _iMatchIdx + 1)
                except Exception as xEx:
                    raise CParserError_ProcRefPath(
                        sContext=f"dictionary element '{sKey}'",
                        lMatch=_lMatch[_iMatchIdx + 1 :],
                        iMatchIdx=0,
                        xChildEx=xEx,
                    )
                # endtry
            # endif xNewVal is None

        else:
            xResult = _xValue
            bLiteral = False
        # endif

        return xResult, bLiteral

    # enddef

    #####################################################################################################
    def _ProcessRefPathListKey(self, _lData, _xKey, _lMatch, _iMatchIdx):
        try:
            iIdx = int(_xKey)
        except Exception:
            iIdx = None
        # endtry
        bLiteral = False
        iDataLen = len(_lData)

        if iIdx is not None:
            iOrigIdx = iIdx
            if iIdx < 0:
                iIdx = iDataLen + iIdx
            # endif

            if iIdx < 0 or iIdx >= iDataLen:
                raise CParserError_Message(
                    sMsg="List index {0} is out of range for list of length {1}.".format(iOrigIdx, iDataLen)
                )
            # endif
            try:
                xResult, bLiteral = self.ProcessRefPath(_lData[iIdx], _lMatch, _iMatchIdx + 1)
            except Exception as xEx:
                raise CParserError_ProcRefPath(
                    sContext="list",
                    lMath=_lMatch[_iMatchIdx + 1 :],
                    iMatchIdx=0,
                    xChildEx=xEx,
                )
            # endtry

        else:
            if isinstance(_xKey, str):
                xSliceMatch = self.reSlice.search(_xKey, 0)

                if xSliceMatch is None:
                    raise CParserError_Message(
                        sMsg="List index for variable '{0}' needs to be an integer, list or slice. Given value is: {1}".format(
                            text.HighlightElementString(_lMatch, _iMatchIdx, ":"), _xKey
                        )
                    )
                # endif

                iFirst = iOrigFirst = int(xSliceMatch.group(1))
                if iFirst < 0:
                    iFirst = iDataLen + iFirst
                    if iFirst < 0:
                        raise CParserError_Message(
                            sMsg="Invalid start index '{}' for list of length {}".format(iOrigFirst, iDataLen)
                        )
                    # endif
                # endif

                iLast = iOrigLast = int(xSliceMatch.group(2))
                if iLast < 0:
                    iLast = iDataLen + iLast
                    if iLast < 0:
                        raise CParserError_Message(
                            sMsg="Invalid last index '{}' for list of length {}".format(iOrigLast, iDataLen)
                        )
                    # endif
                # endif

                if xSliceMatch.group(3) is None:
                    iStep = 1 if iFirst <= iLast else -1
                else:
                    iStep = int(xSliceMatch.group(3))
                # endif
                if iFirst < iLast and iStep <= 0:
                    raise CParserError_Message(sMsg="Step size must be greater than zero in slice.")
                elif iFirst > iLast and iStep >= 0:
                    raise CParserError_Message(sMsg="Step size must be smaller than zero in slice.")
                # endif
                xResult = []
                for iIdx in range(iFirst, iLast + iStep, iStep):
                    try:
                        xData, bLit = self._ProcessRefPathListKey(_lData, iIdx, _lMatch, _iMatchIdx)
                        if bLit is True:
                            bLiteral = True
                        # endif
                        xResult.append(xData)
                    except Exception as xEx:
                        raise CParserError_Message(
                            sMsg=f"Error parsing index {iIdx} of slice '{_xKey}'",
                            xChildEx=xEx,
                        )
                    # endtry
                # endfor

            elif isinstance(_xKey, list):
                xResult = []
                for iKeyIdx, xIdx in enumerate(_xKey):
                    try:
                        xData, bLit = self._ProcessRefPathListKey(_lData, xIdx, _lMatch, _iMatchIdx)
                        if bLit is True:
                            bLiteral = True
                        # endif
                        xResult.append(xData)
                    except Exception as xEx:
                        raise CParserError_Message(
                            sMsg=f"Error parsing index at position {iKeyIdx} of index list: {_xKey}",
                            xChildEx=xEx,
                        )
                    # endtry
                # endfor

            else:
                raise CParserError_Message(
                    sMsg="List index for variable '{0}' needs to be an integer, list or slice".format(
                        text.HighlightElementString(_lMatch, _iMatchIdx, ":")
                    )
                )
            # endif index type
        # endif xKey is an integer

        return xResult, bLiteral

    # enddef


# endclass
