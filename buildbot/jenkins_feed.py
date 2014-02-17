from buildbot.steps.shell import ShellCommand

class JenkinsFeedCommand(ShellCommand):
    def __init__(self,
                jenkins_url,
                jenkins_job,
                jenkins_auth=['jenkins', 'jenkins'],
                #          [<jenkins file parameter name>, <local path> ]
                junit_file=['nosetests.xml', '/tmp/nosetests.xml'],
                coverage_file=['coverage.xml', '/tmp/coverage.xml'],
                **kvs):
        cmd = ['curl',
                jenkins_url + '/job/' + jenkins_job + '/build/',
                '-F file0=@' + junit_file[1],
                '-F file1=@' + coverage_file[1],
                """-F json={"parameter": [{"name": "%s", "file": "file0"}, {"name": "%s", "file": "file1"}]}""" % \
                    (junit_file[0], coverage_file[0]),
                '--user',
                '%s:%s' % (jenkins_auth[0], jenkins_auth[1])]
        ShellCommand.__init__(self, command=cmd, **kvs)
