# -*- encoding: utf-8 -*-
#
# Copyright © 2020–2021 Mergify SAS
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
import logging

import pytest
import yaml

from mergify_engine import context
from mergify_engine.tests.functional import base


LOG = logging.getLogger(__name__)


class TestAttributes(base.FunctionalTestBase):
    async def test_draft(self):
        rules = {
            "pull_request_rules": [
                {
                    "name": "no-draft",
                    "conditions": ["draft"],
                    "actions": {"comment": {"message": "draft pr"}},
                }
            ]
        }
        await self.setup_repo(yaml.dump(rules))

        pr, _ = await self.create_pr()
        ctxt = await context.Context.create(self.repository_ctxt, pr)
        assert not await ctxt.pull_request.draft

        pr, _ = await self.create_pr(draft=True)

        await self.run_engine()
        await self.wait_for("issue_comment", {"action": "created"})

        ctxt = await context.Context.create(
            self.repository_ctxt,
            {
                "number": pr["number"],
                "base": {
                    "user": {"login": pr["base"]["user"]["login"]},
                    "repo": {
                        "name": pr["base"]["repo"]["name"],
                    },
                },
            },
        )
        assert await ctxt.pull_request.draft

        comments = await self.get_issue_comments(pr["number"])
        self.assertEqual("draft pr", comments[-1]["body"])

        # Test underscore/dash attributes
        assert await ctxt.pull_request.review_requested == []

        with pytest.raises(AttributeError):
            assert await ctxt.pull_request.foobar

        # Test items
        assert list(ctxt.pull_request) == list(
            context.PullRequest.ATTRIBUTES | context.PullRequest.LIST_ATTRIBUTES
        )
        assert await ctxt.pull_request.items() == {
            "number": pr["number"],
            "closed": False,
            "locked": False,
            "assignee": [],
            "approved-reviews-by": [],
            "files": ["test2"],
            "check-neutral": [],
            "status-neutral": [],
            "commented-reviews-by": [],
            "milestone": "",
            "label": [],
            "body": "test_draft: pull request n2 from fork",
            "base": self.master_branch_name,
            "review-requested": [],
            "check-success": ["Summary"],
            "status-success": ["Summary"],
            "changes-requested-reviews-by": [],
            "merged": False,
            "head": self.get_full_branch_name("fork/pr2"),
            "author": "mergify-test2",
            "dismissed-reviews-by": [],
            "merged-by": "",
            "check-failure": [],
            "status-failure": [],
            "title": "test_draft: pull request n2 from fork",
            "conflict": False,
        }
