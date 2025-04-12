## Start LLM

Terminal 1:

docker-compose up

Terminal 2: (Run the following commands one by one. Exit each command once you see the "Send a message" prompt)

docker exec -it llm_ollama ollama run llama3.2
docker exec -it llm_ollama ollama run qwen2.5

## Server
start server by running uv run main.py from within the news folder

## Client
start the client by running `uv run .` from the hosts\cli folder


Notes:

Agent Card

Load the agent card by hitting http://localhost:10001/.well-known/agent.json


