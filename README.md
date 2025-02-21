# Stateful Voice Agents  
This repo show how to use Letta and Livekit to create low-latency voice agents with memory, tool execution, and persistence. 

## Installation & Setup 
First install the basic requirements in a virtual enviornment (Python >= 3.10): 
```sh
git clone git@github.com:letta-ai/letta-voice.git
cd letta-voice 
pip install -r requirements.txt
```
You also will to set env vars to configure your accounts with Livekit, Deepgram, Cartesia and OpenAI: 
```sh
LIVEKIT_URL=...
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...

DEEPGRAM_API_KEY=...
CARTESIA_API_KEY=...
OPENAI_API_KEY=...
```

### Running Letta 
To run Letta, you can either install and run [Letta Desktop](https://docs.letta.com/install) or run a Letta service with Docker: 
```
docker run \
  -v ~/.letta/.persist/pgdata:/var/lib/postgresql/data \
  -p 8283:8283 \
  -e OPENAI_API_KEY=${OPENAI_API_KEY} \
  letta/letta:latest
```
See Letta's full quickstart and installation instructions [here](https://docs.letta.com/quickstart).


### Running ngrok 
If the Letta server isn't exposed to the public internet, you can use ngrok to expose it with a static IP:

1. Install ngrok
2. Add your ngrok authtoken with `ngrok config <YOUR-AUTHTOKEN>`
3. Make sure you have a Letta server running at `http://localhost:8283`.
4. Set `LETTA_BASE_URL=http://...`  to your ngrok URL. For example:
```
export LETTA_BASE_URL=https://xxxx.ngrok.app
```

## Running a Voice Agent
0. Make sure you have a Letta server running, with the IP set in `LETTA_BASE_URL`
1. Create an agent with Letta. You can do this in the ADE or via a REST API call. 
2. Set the `LETTA_AGENT_ID=agent-....`, for example: 
```sh
export LETTA_AGENT_ID=agent-xxxxxxx
```
3. Run `python main.py dev`
4. Go to the Livekit Agents Playground: https://agents-playground.livekit.io/
5. Chat with your agent

## Performance 
TODO: notes on performance

## Viewing Agent Interactions 
TODO: ADE demo 
