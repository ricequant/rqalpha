# -*- coding: utf-8 -*-
#
# Copyright 2017 Ricequant, Inc
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import traceback

from six import exec_

from .exception import patch_user_exc, CustomError, CustomException


def compile_strategy(source_code, strategy, scope):
    try:
        code = compile(source_code, strategy, 'exec')
        exec_(code, scope)
        return scope
    except Exception as e:
        exc_type, exc_val, exc_tb = sys.exc_info()
        exc_val = patch_user_exc(exc_val, force=True)
        try:
            msg = str(exc_val)
        except Exception as e1:
            msg = ""
            print(e1)

        error = CustomError()
        error.set_msg(msg)
        error.set_exc(exc_type, exc_val, exc_tb)
        stackinfos = list(traceback.extract_tb(exc_tb))

        if isinstance(e, (SyntaxError, IndentationError)):
            error.add_stack_info(exc_val.filename, exc_val.lineno, "", exc_val.text)
        else:
            for item in stackinfos:
                filename, lineno, func_name, code = item
                if strategy == filename:
                    error.add_stack_info(*item)
            # avoid empty stack
            if error.stacks_length == 0:
                error.add_stack_info(*item)

        raise CustomException(error)
