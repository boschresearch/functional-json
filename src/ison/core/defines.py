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

# RegEx for start of variable expression
reVarStart = re.compile(r"\$(((?P<func>[a-zA-Z_\-*!\?.]*)\{)|((?P<var>[a-zA-Z0-9_]+)(?=[^a-zA-Z0-9_\{]*)))")

# RegEx for a pure variable
rePureVar = re.compile(r"\$((\{(?P<var>[a-zA-Z0-9_]+)\})|((?P<pure>[a-zA-Z0-9_]+)(?![a-zA-Z0-9_.\{])))")

# List slicing syntax: 1~5+2 -> [1, 3, 5]
reSlice = re.compile(r"\s*([+|-]?\d+)~([+|-]?\d+)([+|-]\d+)?")

# RegEx for Lambda Parameter
reLambdaPar = re.compile(r"%(?P<isnull>~?)((?P<name>[a-zA-Z_][a-zA-Z0-9_\-.]*)(:(?P<name_idx>\d+))?%|(?P<idx>\d+))")
reNamedArg = re.compile(r"^\s*(?P<name>[a-zA-Z_][a-zA-Z0-9_\-.]*)\s*(=)\s*(?P<value>.+)")

# RegEx for Lambda Func Call
reLambdaCall = re.compile(r"\$>\{")
reLambdaFunc = re.compile(r"\$L\{")

reString = re.compile(r"\"([^\"]*)\"")
reEscString = re.compile(r"\\\"([^\\\"]*)\\\"")
reLiteralString = re.compile(r"(?<!\\)`(([^`]|\\`)*)(?<!\\)`")

reLiteralArg = re.compile(r"^\s*\^")
reUnrollArg = re.compile(r"^\s*\*\$[a-zA-Z_\{]")
reTupleArg = re.compile(r"^\s*\(")
