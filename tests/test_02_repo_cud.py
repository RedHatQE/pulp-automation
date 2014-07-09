import pulp_test, json, unittest
from pulp_auto.repo import Repo, Importer, Distributor
from pulp_auto.repo import create_yum_repo
from pulp_auto.task import Task


def setUpModule():
    pass


class RepoCudTest(pulp_test.PulpTest):
    @classmethod
    def setUpClass(cls):
        super(RepoCudTest, cls).setUpClass()
        # repo with correct data
        cls.repo = Repo(data={
                        "id": cls.__name__ + "_repo",
                        "notes": {"_repo-type": "rpm-repo"},
                        "distributors": [
                                            {
                                             "distributor_id": "yum_distributor",
                                             "auto_publish": False,
                                             "distributor_type_id": "yum_distributor",
                                             "distributor_config": {"http": False, "relative_url": cls.__name__ + "_repo", "https": True}
                                            }
                                        ],
                        "importer_type_id": "yum_importer",
                        "importer_config": {}
                             }
                        )
        # importer config is missing
        cls.repo1 = Repo(data={
                             "id": cls.__name__ + "_repo1",
                             "notes": {"_repo-type": "rpm-repo"},
                             "distributors": [
                                                 {
                                                  "distributor_id": "yum_distributor",
                                                  "auto_publish": False,
                                                  "distributor_type_id": "yum_distributor",
                                                  "distributor_config": {"http": False, "relative_url": cls.__name__ + "_repo1", "https": True}
                                                 }
                                             ],
                             "importer_type_id": "yum_importer"
                              }
                         )
        # repo with no dist/importer data
        cls.repo2 = Repo(data={'id': cls.__name__ + "_repo2"})
        # relative_url is missing
        cls.repo3 = Repo(data={
                             "id": cls.__name__ + "_repo3",
                             "notes": {"_repo-type": "rpm-repo"},
                             "distributors": [
                                                 {
                                                  "distributor_id": "yum_distributor",
                                                  "auto_publish": False,
                                                  "distributor_type_id": "yum_distributor",
                                                  "distributor_config": {"http": False, "https": True}
                                                 }
                                             ],
                             "importer_type_id": "yum_importer",
                             "importer_config": {}
                              }
                         )


class Bug1078296(RepoCudTest):

    # https://bugzilla.redhat.com/show_bug.cgi?id=1078296
    def test_01_create_repo(self):
        # TODO review how bug was fixed:
        # if importer_config became required key then repo create should fail with code=400
        self.repo1.create(self.pulp)
        self.assertPulpOK()

    @unittest.expectedFailure
    def test_02_update_importer_config_1078296(self):
        response = self.repo1.update(self.pulp, data={"importer_config": {"num_units": 6}})
        self.assertPulp(code=202)
        Task.wait_for_report(self.pulp, response)

    def test_03_delete_repo(self):
        response = self.repo1.delete(self.pulp)
        Task.wait_for_report(self.pulp, response)


class Bug1078340(RepoCudTest):

    # https://bugzilla.redhat.com/show_bug.cgi?id=1078340
    def test_01_create_repo(self):
        self.repo2.create(self.pulp)
        self.assertPulpOK()

    @unittest.expectedFailure
    def test_02_associate_importer_1078340(self):
        # importer_config should be a required key
        self.repo2.associate_importer(self.pulp, data={'importer_type_id': 'yum_importer'})
        self.assertPulp(code=400)

    def test_03_delete_repo(self):
        response = self.repo2.delete(self.pulp)
        Task.wait_for_report(self.pulp, response)


class CUD(RepoCudTest):

    def test_01_create_repo(self):
        self.repo.create(self.pulp)
        self.assertPulpOK()

    def test_02_create_repo_with_missing_parameters(self):
        # "relative_url" from ditributor_config is missing
        self.repo3.create(self.pulp)
        self.assertPulp(code=400)

    def test_03_update_repo_1091348(self):
        # in this custom update you can update repo's info + importer/distributor
        # Seems that after fix of https://bugzilla.redhat.com/show_bug.cgi?id=1091348
        # 202 code will be returned  even when repo is not bound to the consumer,
        # but distributor config is being updated
        response = self.repo.update(self.pulp, data={
                                                   "delta": {"display_name": "NewName"},
                                                   "importer_config": {"num_units": 6},
                                                   "distributor_configs": {
                                                   "yum_distributor": {"relative_url": "my_url"}
                                                                           }
                                                    }
                                   )
        self.assertPulp(code=202)
        Task.wait_for_report(self.pulp, response)

    def test_04_check_update_was_correct(self):
        self.assertEqual(Repo.get(self.pulp, self.repo.id).data['display_name'], "NewName")
        importer = self.repo.get_importer(self.pulp, "yum_importer")
        self.assertEqual(importer.data["config"]["num_units"], 6)
        distributor = self.repo.get_distributor(self.pulp, "yum_distributor")
        self.assertEqual(distributor.data["config"]["relative_url"], "my_url")

    def test_05_delete_repo(self):
        response = self.repo.delete(self.pulp)
        Task.wait_for_report(self.pulp, response)
