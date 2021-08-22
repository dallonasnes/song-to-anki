import multiprocessing
import os

port = int(os.environ.get("PORT", 5000))
bind = "0.0.0.0:" + str(port)

# workers = multiprocessing.cpu_count() * 2 + 1
# max_requests = 1000
# worker_class = 'gevent'
