#### Usage
* copy config files from temp/ directory to ansible/ dir
* export your credentials and set variables in cofig files (see below)
   * export AWS_ACCESS_KEY_ID=\<your_access_key\>
   * export AWS_SECRET_ACCESS_KEY=\<your_secret_access_key\>
* copy your own private key to ./keys/ or generate new keypair using keypair-gen: 
    * ansible-playbook keypair-gen.yml -e @global_vars.yml
* run:
    * ansible-playbook -i ec2.py reposerver-deploy.yml -e @global_vars.yml
    * ansible-playbook -i ec2.py reposerver-run.yml -e @global_vars.yml
* two *.repo files should be present after, containing repositories for installing desired pulp version
* if needed, terminate instance(s) with (s3 bucket will not be deleted)
    * ansible-playbook -i ec2.py ec2-terminate-all.yml -e @global_vars.yml
  

#### Config files
* ansible.cfg -- main ansible config file
* ec2.ini -- ansible dynamic inventory config file
* global_vars.yml -- global variables for use in all playbooks/roles

#### Playbooks
* keypair-gen -- generate new keypair for use in automation, saved to ./keys/
* reposerver -- deploys and configures machine for building pulp (+plugins) rpms from github and  to s3 bucket, generates two *.repo files for later use
* ec2-terminate-all -- serves for terminating all instances, surprisingly
