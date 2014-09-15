import pulp_test, json, unittest
from pulp_auto.repo import RepoAppl
from pulp_auto.task import Task


class RepoApplicabilityTest(pulp_test.PulpTest):
    @classmethod
    def setUpClass(cls):
        super(RepoApplicabilityTest, cls).setUpClass()
        cls.repo_appl = RepoAppl()

class Applicabilty(RepoApplicabilityTest):
    def test_01_repo_content_applicability(self):
        response = self.repo_appl.applicability(self.pulp, data={
                                         "repo_criteria": {"filters": {"id":{"$in":["test-repo", "test-errata"]}}}
                                                     }
                                    )
        self.assertPulp(code=202)
        Task.wait_for_report(self.pulp, response)
        # TODO: assert applicability tags in task response
        # TODO: assert the applicability applies OK :) or is sane

    def test_02_repo_content_applicability_invalid_param(self):
        #response_code: 400,if one or more of the parameters is invalid
        self.repo_appl.applicability(self.pulp, data={
                                         "invalid_parameter": {"filters": {"id":{"$in":["test-repo", "test-errata"]}}}
                                                     }
                                    )
        self.assertPulp(code=400)
