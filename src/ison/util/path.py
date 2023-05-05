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

import os
from typing import Union
from pathlib import Path

from ..core.cls_parser_error import CParserError, CParserError_Message

#######################################################################
def NormPath(_xPath: Union[str, Path]):

    if isinstance(_xPath, str):
        return Path(
            os.path.normpath(os.path.expandvars(os.path.expanduser(_xPath)))
        ).as_posix()

    elif isinstance(_xPath, Path):
        return Path(NormPath(_xPath.as_posix()))

    else:
        raise CParserError_Message(
            sMsg="Path argument has invalid type '{}'".format(
                CParserError.ToTypename(_xPath)
            )
        )
    # endtry


# enddef


#######################################################################
def MakePath(_xParts: Union[str, list, tuple, Path]) -> Path:

    pathX = None

    if isinstance(_xParts, str):
        pathX = Path(_xParts)

    elif isinstance(_xParts, list) or isinstance(_xParts, tuple):
        if len(_xParts) == 0:
            pathX = Path(".")

        else:
            pathX = MakePath(_xParts[0])
            for xPart in _xParts[1:]:
                pathX /= MakePath(xPart)
            # endfor
        # endif

    elif isinstance(_xParts, Path):
        pathX = _xParts

    else:
        pathX = Path(str(_xParts))

    # endif

    return pathX


# enddef

#######################################################################
def MakeNormPath(_xParts: Union[str, list, tuple, Path]) -> Path:
    return NormPath(MakePath(_xParts))


# enddef
