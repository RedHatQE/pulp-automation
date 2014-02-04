from buildbot.steps.shell import ShellCommand

class JenkinsFeedCommand(ShellCommand):
	def __init__(self,
			jenkins_url,
			jenkins_job,
			jenkins_auth=['jenkins', 'jenkins'],
			junit_file='/tmp/nosetests.xml',
			jenkins_file_parameter='nosetests.xml',
			**kvs):
		cmd = ['curl',
			jenkins_url + '/job/' + jenkins_job + '/build/',
			'-F file0=@' + junit_file,
			"""-F json={"parameter": [{"name": "%s", "file": "file0"}]}""" % jenkins_file_parameter,
			'--user',
			'%s:%s' % (jenkins_auth[0], jenkins_auth[1])]
		ShellCommand.__init__(self, command=cmd, **kvs)
