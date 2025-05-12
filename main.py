import asyncio
import logging

import os
from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    llm,
    metrics,
)
from livekit.agents.metrics import PipelineEOUMetrics, PipelineLLMMetrics, PipelineTTSMetrics
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import deepgram, openai, silero, cartesia
from openai import api_key

# Load environment variables
load_dotenv()

# Get environment variables
agent_id = os.getenv('LETTA_AGENT_ID')
ngrok_endpoint = os.getenv('LETTA_ENDPOINT')

logger = logging.getLogger("voice-assistant")


class LatencyTracker:
    """Tracks and stores latency metrics per invocation."""

    def __init__(self):
        self.current_invocation = {"eou_delay": None, "llm_ttft": None, "tts_ttfb": None}
        self.collected_invocations = []

    def update_metric(self, mtrcs: metrics.AgentMetrics):
        """Updates stored metrics for the current invocation based on metric type."""
        if isinstance(mtrcs, PipelineEOUMetrics) and mtrcs.end_of_utterance_delay >= 0:
            self.current_invocation["eou_delay"] = mtrcs.end_of_utterance_delay
        elif isinstance(mtrcs, PipelineLLMMetrics) and mtrcs.ttft >= 0:
            self.current_invocation["llm_ttft"] = mtrcs.ttft
        elif isinstance(mtrcs, PipelineTTSMetrics) and mtrcs.ttfb >= 0:
            self.current_invocation["tts_ttfb"] = mtrcs.ttfb

        # Store once all values are available
        if all(val is not None for val in self.current_invocation.values()):
            self._store_invocation()

    def _store_invocation(self):
        """Stores completed invocation metrics and resets tracker."""
        total_latency = sum(self.current_invocation.values())

        self.collected_invocations.append(
            {
                **self.current_invocation,
                "total_latency": total_latency,
            }
        )
        logger.debug(f"Stored invocation metrics: {self.current_invocation}")

        # Reset for next invocation
        self.current_invocation = {"eou_delay": None, "llm_ttft": None, "tts_ttfb": None}

    def calculate_summary(self):
        """Returns computed summary statistics from collected invocations."""
        if not self.collected_invocations:
            return None

        count = len(self.collected_invocations)
        total_eou = sum(row["eou_delay"] for row in self.collected_invocations)
        total_llm = sum(row["llm_ttft"] for row in self.collected_invocations)
        total_tts = sum(row["tts_ttfb"] for row in self.collected_invocations)
        total_latency = sum(row["total_latency"] for row in self.collected_invocations)

        return {
            "total_invocations": count,
            "avg_eou_delay": total_eou / count,
            "avg_llm_ttft": total_llm / count,
            "avg_tts_ttfb": total_tts / count,
            "avg_total_latency": total_latency / count,
        }


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    initial_ctx = llm.ChatContext().append(
        role="system",
        text="You are a voice assistant that is friendly, brief, and to the point. You should try to ask engaging questions to the user.",
    )

    logger.info(f"Connecting to room {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    participant = await ctx.wait_for_participant()
    logger.info(f"Starting voice assistant for participant {participant.identity}")

    if agent_id and ngrok_endpoint: 
        print(f"Using Letta agent {agent_id}")
        agent = VoicePipelineAgent(
            vad=ctx.proc.userdata["vad"],
            stt=deepgram.STT(),
            llm=openai.LLM(
                # base_url=f"https://823f-104-193-170-185.ngrok-free.app/v1/voice-beta/agent-7785e566-9ad8-4f32-84bb-3d9c36262446",
                base_url=os.getenv("LETTA_ENDPOINT") + "/v1/voice-beta/" + os.getenv("LETTA_AGENT_ID"),
                model=os.getenv("OPENAI_MODEL"),
                # api_key="MTNjYjFkOTctYWViNS00NzU3LTk5YzAtM2M5ZmEzY2U1NTUwOmJlZjMwZjk3LWJmNzMtNGRlNS1iY2U2LTQzMDMxMjM3NWI5Mg==",
                # user="agent-5a26c642-323f-46a6-902b-3dbf37b83c18"
                # user=agent_id
            ),
            tts=cartesia.TTS(),
            chat_ctx=initial_ctx,
        )
    else:
        print("Using OpenAI")
        agent = VoicePipelineAgent(
            vad=ctx.proc.userdata["vad"],
            stt=deepgram.STT(),
            llm=openai.LLM(
                # base_url="https://437c339b175e.ngrok.app/openai/v1",
                model=os.getenv("OPENAI_MODEL"),
                # user="agent-4958c5f7-d47e-447b-981b-3e8d2e2269cf"
            ),
            tts=cartesia.TTS(),
            chat_ctx=initial_ctx,
        )
    agent.start(ctx.room, participant)

    usage_collector = metrics.UsageCollector()
    latency_tracker = LatencyTracker()

    @agent.on("metrics_collected")
    def _handle_metrics_collected(mtrcs: metrics.AgentMetrics):
        """Handles metric collection per invocation."""
        metrics.log_metrics(mtrcs)
        usage_collector.collect(mtrcs)
        latency_tracker.update_metric(mtrcs)

    async def _log_usage_summary():
        """Logs collected usage and invocation latency metrics."""
        summary = usage_collector.get_summary()
        logger.info(f"Usage Summary: {summary}")

        latency_summary = latency_tracker.calculate_summary()
        if latency_summary is None:
            logger.info("No invocation metrics were collected.")
            return

        logger.info("Invocation Metrics Summary:")
        logger.info(f"  Total Invocations: {latency_summary['total_invocations']}")
        logger.info(f"  Average EOU Delay: {latency_summary['avg_eou_delay']:.2f} seconds")
        logger.info(f"  Average LLM TTFT: {latency_summary['avg_llm_ttft']:.2f} seconds")
        logger.info(f"  Average TTS TTFB: {latency_summary['avg_tts_ttfb']:.2f} seconds")
        logger.info(f"  Average Total Latency: {latency_summary['avg_total_latency']:.2f} seconds")

        # Log each invocation
        for idx, row in enumerate(latency_tracker.collected_invocations, start=1):
            logger.info(
                f"Invocation {idx}: "
                f"EOU Delay = {row['eou_delay']:.2f}s, "
                f"LLM TTFT = {row['llm_ttft']:.2f}s, "
                f"TTS TTFB = {row['tts_ttfb']:.2f}s, "
                f"Total Latency = {row['total_latency']:.2f}s"
            )

    ctx.add_shutdown_callback(_log_usage_summary)

    await agent.say("Hi! What's your name?", allow_interruptions=True)


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
        ),
    )
