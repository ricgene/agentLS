
remote is agentLS
# see .env-example

Test locally:
cd ~/gitl/pz2/hello-graph

# to run workflow.py locally in studio
poetry run langgraph dev
https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
# then paste input data from workflow2.py file into studio input.

poetry run python workflow2.py

# incorporate query-trace-filter-out-scanned.py
poetry run python query-langgraph.py

Test in the cloud:
Deploy:
   https://smith.langchain.com/o/fa54f251-75d3-4005-8788-376a48b2c6c0/host/deployments
   Repo: has to be public?  or can give langgraph my git key...
       https://github.com/ricgene/pz2

https://smith.langchain.com/studio/thread




#later, separately - let's see
poetry run test-agent-local-studio-nostream.py
