from faktory import Worker
from jobs.master_environments import environments_sync
from jobs.master_facts import facts_sync
from jobs.master_nodes import nodes_sync
from jobs.master_classes import classes_sync
from jobs.matching_nodes import matching_nodes_sync

w = Worker(queues=["default"], concurrency=1)
w.register("master-environments", environments_sync)
w.register("master-facts", facts_sync)
w.register("master-nodes", nodes_sync)
w.register("master-classes", classes_sync)
w.register("group-nodes", matching_nodes_sync)
w.run()
