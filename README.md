# Stateful Voice Agents

This repo show how to use Letta and Livekit to create low-latency voice agents with memory, tool execution, and persistence.

## Installation & Setup

First install the basic requirements in a virtual enviornment (Python >= 3.10):

```
git clone git@github.com:letta-ai/letta-voice.git
cd letta-voice
pip install -r requirements.txt
```

You also will to set env vars to configure your accounts with Livekit, Deepgram, and Cartesia:

```
LIVEKIT_URL=
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...

DEEPGRAM_API_KEY=...
CARTESIA_API_KEY=...
```

## Connecting Letta to Voice

1. Set `LETTA_ENDPOINT` to your Letta endpoint, for example:

```
export LETTA_ENDPOINT=
```

2. Set the `LETTA_AGENT_ID=agent-....` to the agent backend, for example:

```
export LETTA_AGENT_ID=agent-xxxxxxx
```

3. Run `python main.py dev`
4. Go to the Livekit Agents Playground: https://agents-playground.livekit.io/
5. Chat with your agent

## Running Letta (Optional: only if you don't have cloud access)

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

1. Install ngrok
2. Add your ngrok authtoken with `ngrok config <YOUR-AUTHTOKEN>`
3. Make sure you have a Letta server running at `http://localhost:8283`.
4. Set `LETTA_ENDPOINT=http://...` to your ngrok URL. For example:

```
export LETTA_ENDPOINT=https://xxxx.ngrok.app
```

## Performance

TODO: notes on performance

## Viewing Agent Interactions

TODO: ADE demo

# Running the demo

1. Copy the environment variables in `.env.template` to `.env`. Fill in the values. Export the variables.
2. Run Letta docker with the OPENAI_API_KEY
3. Run ngrok with instructions above
4. Run `python main.py dev`
5. cd frontend
6. Run `npm run dev`
7. Open `http://localhost:5173` and chat with your agent
