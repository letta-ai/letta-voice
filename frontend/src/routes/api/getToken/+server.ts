import { json } from "@sveltejs/kit";
import { AccessToken } from "livekit-server-sdk";

/** @type {import('./$types').RequestHandler} */
export async function GET() {
  const roomName = "quickstart-room";
  const participantName = "quickstart-username";

  const at = new AccessToken(
    process.env.LIVEKIT_API_KEY,
    process.env.LIVEKIT_API_SECRET,
    {
      identity: participantName,
      ttl: "10m",
    }
  );
  at.addGrant({ roomJoin: true, room: roomName });

  const token = await at.toJwt();
  return json({
    value: token,
    wsURL: process.env.LIVEKIT_URL,
  });
}
