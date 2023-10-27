import docker

client = docker.from_env()
container_list = client.containers.list()
print(container_list)
# print(type(container_list[0]))
# print(container_list[0].status)
# print(client.containers.get("garbagefall_v"))
