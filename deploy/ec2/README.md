### Deployment notes
- use Fedora 20
- disk size >= 16GB
- feed fedora_pulp_buildbot.sh as user data
- logs: /var/log/fedora_pulp.log
- re-run: /var/lib/cloud/instance/scripts/part-001
- Security group: add HTTP, HTTPS, SSH, 5672 for qpid and 5673 for rabbitmq ports
