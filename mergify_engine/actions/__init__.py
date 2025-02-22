# -*- encoding: utf-8 -*-
#
#  Copyright © 2018—2020 Mergify SAS
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

import abc
import dataclasses
import typing

import pkg_resources
import voluptuous

from mergify_engine import check_api
from mergify_engine import context
from mergify_engine import rules


global _ACTIONS_CLASSES
_ACTIONS_CLASSES: typing.Optional[typing.Dict[str, "Action"]] = None

ActionSchema = typing.NewType("ActionSchema", voluptuous.All)  # type: ignore


def get_classes() -> typing.Dict[str, "Action"]:
    global _ACTIONS_CLASSES
    if _ACTIONS_CLASSES is None:
        _ACTIONS_CLASSES = {
            ep.name: ep.load()
            for ep in pkg_resources.iter_entry_points("mergify_actions")
        }
    return _ACTIONS_CLASSES


def get_action_schemas() -> typing.Dict[str, ActionSchema]:
    return {
        name: obj.get_schema() for name, obj in get_classes().items() if obj.is_action
    }


def get_commands() -> typing.Dict[str, "Action"]:
    return {name: obj for name, obj in get_classes().items() if obj.is_command}


class EvaluatedActionRule(typing.NamedTuple):
    reason: str
    conditions: "rules.RuleConditions"
    missing_conditions: "rules.RuleMissingConditions"


@dataclasses.dataclass  # type: ignore
class Action(abc.ABC):
    is_action = True
    is_command = False

    always_run = False

    # FIXME: this might be more precise if we replace voluptuous by pydantic somehow?
    config: typing.Dict[str, typing.Any]

    cancelled_check_report = check_api.Result(
        check_api.Conclusion.CANCELLED,
        "The rule doesn't match anymore",
        "This action has been cancelled.",
    )

    # If an action can't be twice in a rule this must be set to true
    only_once = False

    # If set to True, does not post the report to the Check API
    # Only keep it for internal tracking
    silent_report = False

    # This makes checks created by mergify retriggering Mergify, beware to
    # not create something that endup with a infinite loop of events
    allow_retrigger_mergify = False

    @property
    @staticmethod
    @abc.abstractmethod
    def validator() -> typing.Dict[typing.Any, typing.Any]:  # pragma: no cover
        pass

    def validate_config(
        self, mergify_config: "rules.MergifyConfig"
    ) -> None:  # pragma: no cover
        pass

    @classmethod
    def get_schema(cls) -> ActionSchema:
        return ActionSchema(
            voluptuous.All(
                voluptuous.Coerce(lambda v: {} if v is None else v),
                cls.validator,
                voluptuous.Coerce(cls),
            )
        )

    @staticmethod
    def command_to_config(string: str) -> typing.Dict[str, typing.Any]:
        """Convert string to dict config"""
        return {}

    async def run(
        self, ctxt: context.Context, rule: "rules.EvaluatedRule"
    ) -> check_api.Result:  # pragma: no cover
        pass

    async def cancel(
        self, ctxt: context.Context, rule: "rules.EvaluatedRule"
    ) -> check_api.Result:  # pragma: no cover
        return self.cancelled_check_report

    async def get_rule(
        self,
        ctxt: context.Context,
    ) -> EvaluatedActionRule:  # pragma: no cover
        return EvaluatedActionRule(
            "", rules.RuleConditions([]), rules.RuleMissingConditions([])
        )

    @staticmethod
    async def wanted_users(
        ctxt: context.Context, users: typing.List[str]
    ) -> typing.List[str]:
        wanted = set()
        for user in set(users):
            try:
                user = await ctxt.pull_request.render_template(user)
            except context.RenderTemplateFailure:
                # NOTE: this should never happen since
                # the template is validated when parsing the config 🤷
                continue
            else:
                wanted.add(user)

        return list(wanted)
