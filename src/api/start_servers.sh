#!/bin/bash

# Start expose_server.py in the background
python3 src/api/expose_server.py &

# Start basic_backend_server.py in the background
python3 src/api/basic_backend_server.py &

# Wait for all background processes to finish
wait
