# -*- encoding: utf-8 -*-
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
import typing

from mergify_engine import actions
from mergify_engine import check_api
from mergify_engine import context
from mergify_engine import rules
from mergify_engine import utils


class RefreshAction(actions.Action):
    is_command = True
    is_action = False
    validator: typing.ClassVar[typing.Dict[typing.Any, typing.Any]] = {}

    async def run(
        self, ctxt: context.Context, rule: rules.EvaluatedRule
    ) -> check_api.Result:
        with utils.aredis_for_stream() as redis_stream:
            await utils.send_refresh(
                ctxt.redis,
                redis_stream,
                ctxt.pull["base"]["repo"],
                pull_request_number=ctxt.pull["number"],
            )
        return check_api.Result(
            check_api.Conclusion.SUCCESS, title="Pull request refreshed", summary=""
        )
