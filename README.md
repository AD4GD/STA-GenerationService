## Environment setup

#### First run

Run following command:

    ./devstack config

It will create `compose/.env` file after prompting to specify docker registry to use, etc.
It will also create empty `compose/local.yaml` file.

In fact running any compose script will create those file if they are missing.

One should read carefully output of `./devstack config` to check resolved parameters correctness.

#### Environment variables

Docker compose files are expecting the following environment variables:

* REGISTRY_DOMAIN -- most likely `registry.paas.psnc.pl`
* IMAGE_TAG -- most likely `branch-develop`
* REPO_DIR -- location of the repo (when using docker-machine it should be path inside virtual machine)

This variables should be defined in [`compose/.env`][1] file.
Their definition in some kind of shell alias or script is probably also possible but not officialy supported.

#### IMAGE_TAG

IMAGE_TAG environment variable can be filled for:
* specific remote branch, e.g. for branch "test_solution" IMAGE_TAG shoud be set to "branch-test_solution",
* specific commit from repository, e.g. for commit hash "1f6876ec4785a3f8de65287bd58d962f562ecfb1" IMAGE_TAG should be set to "commit-1f6876ec4785a3f8de65287bd58d962f562ecfb1",
* image built locally, that won't be pushed to registry - IMAGE_TAG should be set to "local-build".

For IMAGE_TAG variable slashes ("/") should be replaced with dashes ("-"), e.g. for branch "test/solution" IMAGE_TAG should be set to "branch-test-solution".

#### Instance settings

One may use `compose/local.yaml` file, where should go every runtime parameters specific to the local instance.
File must be proper compose file, which must include at least version numer. This file is not tracked in git.
This file is automatically created on first run.

#### Domain name

One must setup local domain name resolution for the project's domain. It could be done by adding docker machine IP address to the _hosts_ file:

* `/etc/hosts` -- on unix;
* `c:\windows\system32\drivers\etc\hosts` -- on windows.


    # check machines IP address
    $ docker-machine ip [machine name]
    192.168.99.100

    # line to add to hosts file
    192.168.99.100  localhost.sta


## Running development stack

    cd bin
    ./devstack up

After above command is run, server should listen at: http://localhost.sta.
Any changes made in the source files will be available without a need for restarting containers.

#### First run

After first project start-up, database migration could be needed:

    ./devstack exec django manage migrate

## Running tests

Run default tests with code coverage:

    cd bin
    ./devtests run django

#### Additional py.test arguments

    ./devtests run django py.test -vv -x -k some_test

#### Running test coverage (also accepts py.test arguments)

    ./devtests run django test.coverage -vv -x

#### Interactive shell

    ./devtests run django bash


## Code audit

#### Code quality audit
Code audit command is used to keep good code quality during development.
Audit can be run locally by executing below command. Existing problems will be printed out to the standard output.

    source venv/bin/activate
    pip install pre-commit
    pre-commit run -a
Confuguration of pre-commit tool is done in file .pre-commit-config.yaml.

#### Packages dependencies compatibility
Compatibility of required packages' dependencies could be checked with command:

    ./devaudit run dependencies-pip-check

#### Vulnerability check
It is possible to find known vulnerabilities for current project (requirements file).
Python package "safety" (https://github.com/pyupio/safety) is used with default vulnerabilities database from https://pyup.io/
Vulnerability check can be run by typing:

    ./devaudit run vulnterability-check

#### Django deployment potential problems detection

Potential django problems with deployment settings can be detected by typing:

    ./devaudit run manage-check

#### Check packages licenses

Config file licenses.ini contains list of authorized license types for installed python packages. You can perform licenses audit for project by typing:

    ./devaudit run license-check

All available licenses can be found here: https://pypi.org/pypi?%3Aaction=list_classifiers
Edit licenses.ini file to add new authorized license type.

#### Security check

Security audit for current project can be run by typing

    ./devtests run security-check

Config file bandit.ini contains test types that should be run or skipped. Test types are available here: https://bandit.readthedocs.io/en/stable/plugins/index.html#complete-test-plugin-listing

## Openshift deployment

### Prerequisites

Deployment configurations requires kubernetes cluster with configured dynamic volume provisioning.

Deployment is based on ansible playbooks -- every ansible command requires inventory file
which can be specified with environment variable:

    export ANSIBLE_INVENTORY=<absolute path to inventory file>

### First time configuration

Configure docker secret for pulling images in openshift project:

    oc create secret docker-registry regcred --docker-server=registry.paas.psnc.pl --docker-username=<...> --docker-password=<...>
    oc secrets add serviceaccount/default secrets/regcred --for=pull

Set name of the secret created above in the inventory as `image_pull_secret`.

### Code deployment

First and each subsequent deployment is run performed using command:

    ansible-playbook -i <inventory-file> -e image_tag=<...> deploy-all-and-test.yaml

During deployment process playbook checks for existance of some global settings (like docker registry secret) and if those settings are not provided, it will stop and ask for action.

See [docs/deployment.md](docs/deployment.md) more information.

### Certificates
TO DO

## References

[1]: https://docs.docker.com/compose/env-file/
