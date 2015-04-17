Pulp-Automation
===============

Some pulp API/CLI testing automation

Contents:
---------
/deploy - thereis an ansible and ec2 pulp deployment

/tests  - pulp api/cli testcases

/pulp_auto - our library


Requirements for running:
-------------------------

Please make sure that before running setup.py you have `python2.7, python-devel, m2crypto and gcc installed`!

    python ./setup.py install


Basic usage:
------------

To run tests:

1) copy the inventory.yml from the directory /tests into /pulp-automation and edit it. How to do it properly you can find info in the file itself.

2) To run all tests:

    nosetests -vs
    
   To run a particular test:

    nosetests -vs tests/test_1_login.py

All testcases should pass. If something fails it means that:
  - there is a regression bug,
  - some bugs are on_qa state and expected failure decorator(used to mark automated BZ tests as pass) should be removed,
  - there is a problem in the framework


To do test coverage:
--------------------

    -place .coveragerc into /usr/share/pulp_auto

Docker usage
------------
To run, set the env variable `PULPHOST` to override packaged `inventory.yaml` entries:
`docker run -it -e PULPHOST=pulp.example.com dparalen/pulp-automation:latest`
The default pulp hostname used in the inventory is `pulp.example.com`
Setting up hostnames resolution should also make the tests run.

The pulp-automation image uses a volume--workdir to run nosetest in.
You can find the test results in the workdir counterpart on your docker host, such as:
`/mnt/sda1/var/lib/docker/vfs/dir/<container ID>/`
Having run the container, you should find e.g. `nosetests.xml` inside, which you could feed to your `Jenkins` server.
 
