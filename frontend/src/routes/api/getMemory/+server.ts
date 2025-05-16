import { LettaClient } from "@letta-ai/letta-client";
import type { Block, Passage } from "@letta-ai/letta-client/api";
import { json } from "@sveltejs/kit";

export async function GET() {
  if (!process.env.LETTA_ACCESS_TOKEN || !process.env.LETTA_BASE_URL) {
    return json(
      { error: "Missing Letta access token or server URL" },
      { status: 500 }
    );
  }

  // if (!process.env.LETTA_COMPANION_AGENT_ID) {
  //   return json({ error: "Missing Letta voice agent ID" }, { status: 404 });
  // }

  const client = new LettaClient({
    token: process.env.LETTA_ACCESS_TOKEN,
    baseUrl: process.env.LETTA_BASE_URL,
  });
  const agentId = "agent-473cd30c-6ef1-4d45-8369-f86da5578c34";

  const agent = await client.agents.retrieve(agentId);
  const memory = agent.memory.blocks;

  const formattedCoreMemory = memory.map((block: Block) => {
    if (!block.label) {
      return;
    }
    return {
      [block.label]: block.value,
    };
  });

  const archivalMemory = await client.agents.passages.list(agentId);

  const formattedArchivalMemory = archivalMemory.map((passage: Passage) => {
    return {
      [passage.createdAt!.toISOString()]: passage.text,
    };
  });

  return json({ core: formattedCoreMemory, archival: formattedArchivalMemory });
}
