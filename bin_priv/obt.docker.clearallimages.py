#!/usr/bin/env python3
from obt import command, docker

#command.Command(["docker","rm","-vf","$(docker ps -aq)"],do_log=True).exec(use_shell=True);
#command.Command(["docker","rmi","-f","$(docker images -aq)"],do_log=True).exec(use_shell=True);

container_list = docker.enumerate_all_continaers()
image_list = docker.enumerate_all_images()
print("containers: %s"%container_list)
print("images: %s" % image_list)

for item in container_list:
  command.run(["docker","kill",item],do_log=True)
for item in container_list:
  command.run(["docker","rm","-vf", item],do_log=True)  

for item in image_list:
  command.run(["docker","rmi","-f", item],do_log=True)  

command.run(["docker", "system", "prune", "-a"],do_log=True)