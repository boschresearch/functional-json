#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: /ison/util/convert.py
# Created Date: Friday, March 4th 2022, 10:44:00 am
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

############################################################################################
def ToBool(xValue):

    if isinstance(xValue, bool):
        return xValue
    # endif

    if isinstance(xValue, str):
        if xValue == "true":
            return True
        elif xValue == "false":
            return False
        else:
            raise RuntimeError(
                "Cannot convert string '{}' to boolean. Expect 'true' or 'false'".format(
                    xValue
                )
            )
        # endif
    # endif

    if isinstance(xValue, int):
        return xValue != 0
    # endif

    if isinstance(xValue, float):
        return xValue != 0.0
    # endif

    raise RuntimeError("Cannot convert given element to boolean: {}".format(xValue))


# enddef


#######################################################################
# Cast to integer
def ToInt(_xValue, iDefault=None, bDoRaise=True):

    try:
        iResult = int(_xValue)

    except Exception:
        if isinstance(iDefault, int):
            return iDefault
        # endif

        if bDoRaise is True:
            raise RuntimeError(f"Error converting '{_xValue}' to integer.")
        else:
            return None
        # endif
    # endtry

    return iResult


# enddef


#######################################################################
# Cast to float
def ToFloat(_xValue, fDefault=None, bDoRaise=True):
    try:
        fResult = float(_xValue)
    except Exception:
        if isinstance(fDefault, float):
            return fDefault
        # endif

        if bDoRaise is True:
            raise RuntimeError(f"Error converting '{_xValue}' to float.")
        else:
            return None
        # endif
    # endtry

    return fResult


# enddef
