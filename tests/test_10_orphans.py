import pulp_test, json, pprint, pulp_auto
from pulp_auto.repo import create_yum_repo, Repo
from pulp_auto.task import Task
from pulp_auto.orphan import Orphans, OrphanFactory, RpmOrphan
 
def setUpModule():
    pass


class SimpleOrphanTest(pulp_test.PulpTest):

    @classmethod
    def setUpClass(cls):
        super(SimpleOrphanTest, cls).setUpClass()
        # prepare orphans
        feed = 'http://repos.fedorapeople.org/repos/pulp/pulp/demo_repos/zoo/'
        repo_name = cls.__name__ + '_repo'
        repo = Repo({'id': repo_name})
        repo.delete(cls.pulp)
        cls.repo = create_yum_repo(cls.pulp, repo_name, feed, relative_url=repo_name)[0]
        sync_task = Task.from_response(cls.repo.sync(cls.pulp))[0]
        sync_task.wait(cls.pulp)
        # this is where orphans appear
        cls.repo.delete(cls.pulp)

    def test_00_get_orphan_info(self):
        Orphans.info(self.pulp)
        self.assertPulpOK()

    def test_01_orphan_info_data_integrity(self):
        info = Orphans.info(self.pulp)
        orphans = Orphans.get(self.pulp)
        self.assertPulpOK()
        for orphan_type_name in orphans.keys():
            # reported count info is the same as the orphans counted
            self.assertEqual(len(orphans[orphan_type_name]), info[orphan_type_name]['count'])
            orphan_type = OrphanFactory.type_map[orphan_type_name]
            # '_href' is correct
            self.assertEqual(pulp_auto.path_join(pulp_auto.path, orphan_type.path), info[orphan_type_name]['_href'])
            # all orphans are of the same type
            for orphan in orphans[orphan_type_name]:
                self.assertTrue(isinstance(orphan, orphan_type), "different type: %s, %s" % (orphan_type_name, orphan.type_id))

    def test_02_delete_single_orphan(self):
        old_info = Orphans.info(self.pulp)
        rpm_orphans = RpmOrphan.list(self.pulp)
        rpm_orphans[0].delete(self.pulp)
        del rpm_orphans[0]
        self.assertPulpOK()
        new_info = Orphans.info(self.pulp)
        self.assertEqual(old_info['rpm']['count'], new_info['rpm']['count'] + 1)
        self.assertEqual(
            sorted(map(lambda x: x.data['name'], rpm_orphans)),
            sorted(map(lambda x: x.data['name'], RpmOrphan.list(self.pulp)))
        )
        
 
    def test_03_delete_orphans(self):
        delete_response = Orphans.delete(self.pulp)
        self.assertPulpOK()
        delete_task = Task.from_response(delete_response)
        delete_task.wait(self.pulp)
        info = Orphans.info(self.pulp)
        orphans = Orphans.get(self.pulp)
        self.assertPulpOK()
        for orphan_type_name in info.keys():
            self.assertEqual(len(orphans[orphan_type_name]), info[orphan_type_name]['count'])
            self.assertEqual(orphans[orphan_type_name], [])

    @classmethod
    def tearDownClass(cls):
        pass
