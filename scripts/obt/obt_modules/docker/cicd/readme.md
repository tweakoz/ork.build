this docker module requires secrets
pass in secrets to obt.docker commands by the SECRETSDIR environment variable.

eg.

SECRETSDIR=/path/to/secrets obt.docker.build.py cicd

SECRETSDIR=/path/to/secrets obt.docker.launch.py cicd