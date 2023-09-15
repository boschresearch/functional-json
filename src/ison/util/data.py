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

import re
import copy
import platform


################################################################################
def AssertDisjunctVarDicts(_dicA, _dicB, _sNameA, _sNameB):
    # test whether dictionaries have no top-level elements in common
    if _dicA is not None and _dicB is not None:
        for sItem in _dicA:
            if sItem in _dicB:
                raise Exception(
                    "Variable '{0}' defined in {3} and {4}:\n"
                    "In {3}: {1}\n"
                    "In {4}: {2}\n".format(sItem, _dicA[sItem], _dicB[sItem], _sNameA, _sNameB)
                )
            # endif
        # endfor
    # endif


# enddef


################################################################################
# update dictionary and potentially throw exception when overwriting a variable
def UpdateDict(
    _dicTrg,
    _dicSrc,
    _sContext,
    bAllowOverwrite=False,
    bThrowOnDisallow=True,
    bPrintWarnings=True,
    bIgnoreSpecialVars=False,
    bCopyData=True,
):
    for sId, xSrcEl in _dicSrc.items():
        if bIgnoreSpecialVars is True and sId.startswith("__"):
            continue
        # endif

        if sId in _dicTrg:
            if isinstance(_dicTrg[sId], dict) and isinstance(xSrcEl, dict):
                # Recursively update dictionaries if they are present in source and target
                UpdateDict(
                    _dicTrg[sId],
                    xSrcEl,
                    _sContext,
                    bAllowOverwrite=bAllowOverwrite,
                    bThrowOnDisallow=bThrowOnDisallow,
                    bPrintWarnings=bPrintWarnings,
                )
            else:
                if bAllowOverwrite is False:
                    sMsg = "Attempt to overwrite dictionary element '{0}' " "disallowed during update of {1}".format(
                        sId, _sContext
                    )

                    if bThrowOnDisallow is True:
                        raise Exception(sMsg)
                    else:
                        if bPrintWarnings is True:
                            print("Warning: " + sMsg)
                        # endif
                    # endif

                else:
                    if bPrintWarnings is True:
                        sMsg = "Overwriting dictionary element '{0}' during " "update of {1}".format(sId, _sContext)
                        print("Warning: " + sMsg)
                        # print("Source: {}".format(_dicSrc[sId]))
                        # print("Target: {}".format(_dicTrg[sId]))
                    # endif

                    if bCopyData is True:
                        _dicTrg[sId] = copy.deepcopy(xSrcEl)
                    else:
                        _dicTrg[sId] = xSrcEl
                    # endif
                # endif
            # endif
        else:
            if bCopyData is True:
                _dicTrg[sId] = copy.deepcopy(xSrcEl)
            else:
                _dicTrg[sId] = xSrcEl
            # endif
        # endif
    # endfor


# enddef


################################################################################
def AddVarsToData(
    _xData,
    dicGlobals=None,
    dicLocals=None,
    dicEvalGlobals=None,
    dicEvalLocals=None,
    dicFuncGlobals=None,
    dicFuncLocals=None,
    bAllowOverwrite=False,
    bThrowOnDisallow=True,
    bPrintWarnings=True,
):
    if isinstance(dicLocals, dict):
        if "__locals__" in _xData:
            UpdateDict(
                _xData["__locals__"],
                dicLocals,
                "locals",
                bAllowOverwrite=bAllowOverwrite,
                bThrowOnDisallow=bThrowOnDisallow,
                bPrintWarnings=bPrintWarnings,
            )
        else:
            _xData["__locals__"] = dicLocals
        # endif
    # endif

    if isinstance(dicEvalLocals, dict):
        if "__eval_locals__" in _xData:
            UpdateDict(
                _xData["__eval_locals__"],
                dicEvalLocals,
                "evaluated locals",
                bAllowOverwrite=bAllowOverwrite,
                bThrowOnDisallow=bThrowOnDisallow,
                bPrintWarnings=bPrintWarnings,
            )
        else:
            _xData["__eval_locals__"] = dicEvalLocals
        # endif
    # endif

    if isinstance(dicGlobals, dict):
        if "__globals__" in _xData:
            UpdateDict(
                _xData["__globals__"],
                dicGlobals,
                "globals",
                bAllowOverwrite=bAllowOverwrite,
                bThrowOnDisallow=bThrowOnDisallow,
                bPrintWarnings=bPrintWarnings,
            )
        else:
            _xData["__globals__"] = dicGlobals
        # endif
    # endif

    if isinstance(dicEvalGlobals, dict):
        if "__eval_globals__" in _xData:
            UpdateDict(
                _xData["__eval_globals__"],
                dicEvalGlobals,
                "evaluated globals",
                bAllowOverwrite=bAllowOverwrite,
                bThrowOnDisallow=bThrowOnDisallow,
                bPrintWarnings=bPrintWarnings,
            )
        else:
            _xData["__eval_globals__"] = dicEvalGlobals
        # endif
    # endif

    if isinstance(dicFuncGlobals, dict):
        if "__func_globals__" in _xData:
            UpdateDict(
                _xData["__func_globals__"],
                dicFuncGlobals,
                "function globals",
                bAllowOverwrite=bAllowOverwrite,
                bThrowOnDisallow=bThrowOnDisallow,
                bPrintWarnings=bPrintWarnings,
            )
        else:
            _xData["__func_globals__"] = dicFuncGlobals
        # endif
    # endif

    if isinstance(dicFuncLocals, dict):
        if "__func_locals__" in _xData:
            UpdateDict(
                _xData["__func_locals__"],
                dicFuncLocals,
                "function locals",
                bAllowOverwrite=bAllowOverwrite,
                bThrowOnDisallow=bThrowOnDisallow,
                bPrintWarnings=bPrintWarnings,
            )
        else:
            _xData["__func_locals__"] = dicFuncLocals
        # endif
    # endif


# enddef


################################################################################
# Add local and global variables from one dict to another
def AddLocalGlobalVars(
    _dicTrg,
    _dicSrc,
    bAllowOverwrite=False,
    bThrowOnDisallow=True,
    bPrintWarnings=True,
    bLocalVars=True,
    bGlobalVars=True,
):
    AddVarsToData(
        _dicTrg,
        dicGlobals=_dicSrc.get("__globals__") if bGlobalVars is True else None,
        dicLocals=_dicSrc.get("__locals__") if bLocalVars is True else None,
        dicEvalGlobals=_dicSrc.get("__eval_globals__") if bGlobalVars is True else None,
        dicEvalLocals=_dicSrc.get("__eval_locals__") if bLocalVars is True else None,
        dicFuncGlobals=_dicSrc.get("__func_globals__") if bGlobalVars is True else None,
        dicFuncLocals=_dicSrc.get("__func_locals__") if bLocalVars is True else None,
        bAllowOverwrite=bAllowOverwrite,
        bThrowOnDisallow=bThrowOnDisallow,
        bPrintWarnings=bPrintWarnings,
    )


# enddef


################################################################################
def ConstructRegExFromWildcards(_lWildcards) -> list[re.Pattern]:
    # Construct regular expressions from box types
    lRegEx = []
    for sWildcard in _lWildcards:
        if len(sWildcard) == 0:
            continue
        # endif
        sWildcard = sWildcard.replace(".", r"\.")
        if sWildcard[-1] == "*":
            sWildcard = sWildcard[0:-1].replace("*", r"[\w]*") + r"[\w\.]*"
        else:
            sWildcard = sWildcard.replace("*", r"[\w]*")
        # endif
        sWildcard = sWildcard.replace("?", ".")
        lRegEx.append(re.compile(sWildcard))
    # endfor

    return lRegEx


# enddef


################################################################################
# Get Dictionary for current system/node
def GetPlatformDict(_dicData):
    dicPlatform = _dicData.get("__platform__")
    if dicPlatform is None:
        return _dicData
    # endif

    dicNode = None
    dicSystem = dicPlatform.get(platform.system())
    if isinstance(dicSystem, dict):
        lNodes: list[str] = [x for x in dicSystem.keys() if not x.startswith("__")]
        lRegEx = ConstructRegExFromWildcards(lNodes)
        sNode = platform.node()
        xRegEx: re.Pattern
        for iIdx, xRegEx in enumerate(lRegEx):
            xMatch = xRegEx.fullmatch(sNode)
            if xMatch is not None:
                dicNode = dicSystem.get(lNodes[iIdx])
                break
            # endif
        # endfor
        # dicNode = dicSystem.get(platform.node())
    else:
        dicSystem = None
    # endif

    # Consolidate data for current node/system
    dicActData = {}
    for sId in _dicData:
        if sId == "__platform__":
            continue
        # endif
        dicActData[sId] = _dicData[sId]
    # endfor

    if dicSystem is not None and "__data__" in dicSystem:
        dicActData.update(dicSystem["__data__"])
    # endif

    if dicNode is not None and "__data__" in dicNode:
        dicActData.update(dicNode["__data__"])
    # endif

    return dicActData


# enddef


################################################################################
# Strip variables from dictionary recursively
def StripVarsFromData(_xData):
    lVarKeys = [
        "__globals__",
        "__eval_globals__",
        "__locals__",
        "__eval_locals__",
        "__func_globals__",
        "__func_locals__",
        "__runtime_vars__",
    ]

    if isinstance(_xData, dict):
        xResult = {}
        for sKey in _xData:
            if sKey in lVarKeys:
                continue
            # endif
            xResult[sKey] = StripVarsFromData(_xData[sKey])
        # endfor

    elif isinstance(_xData, list):
        xResult = []
        for xEl in _xData:
            xResult.append(StripVarsFromData(xEl))
        # endfor

    else:
        xResult = _xData
    # endif

    return xResult


# enddef
