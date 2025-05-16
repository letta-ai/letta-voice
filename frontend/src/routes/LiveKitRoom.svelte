<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import { tick } from "svelte";
  import {
    Room,
    RemoteTrack,
    Track,
    RoomEvent,
    RemoteParticipant,
    Participant,
    ConnectionState,
    TrackPublication,
    type TranscriptionSegment,
  } from "livekit-client";
  import type { Passage } from "@letta-ai/letta-client/api";
  import { slide } from "svelte/transition";

  let token: { value: string; wsURL: string } | null = null;
  let memory: {
    core: { label: string; value: string }[];
    archival: Passage[];
  } | null = null;

  let room: Room;
  let audioElements: Map<string, HTMLAudioElement> = new Map();
  let connected = false;
  let transcriptions: { [id: string]: TranscriptionSegment } = {};

  let buttonShouldBounce = true;
  let showGlow = false;
  let isMemoryExpanded = false;

  function handleTranscriptionReceived(
    segments: TranscriptionSegment[],
    participant?: Participant,
    publication?: TrackPublication
  ) {
    for (const segment of segments) {
      transcriptions[segment.id] = segment;
    }

    tick().then(() => {
      const container = document.getElementById("transcription-container");
      if (container) {
        container.scrollTop = container.scrollHeight;
      }
    });
  }

  function handleTrackSubscribed(
    track: RemoteTrack,
    publication: any,
    participant: RemoteParticipant
  ) {
    if (track.kind === Track.Kind.Audio) {
      const audioElement = new Audio();
      audioElement.srcObject = new MediaStream([track.mediaStreamTrack]);
      audioElement.autoplay = true;
      audioElements.set(participant.sid, audioElement);
      document.body.appendChild(audioElement);
    }
  }

  function handleTrackUnsubscribed(
    track: RemoteTrack,
    publication: any,
    participant: RemoteParticipant
  ) {
    if (track.kind === Track.Kind.Audio) {
      const audioElement = audioElements.get(participant.sid);
      if (audioElement) {
        audioElement.srcObject = null;
        audioElement.remove();
        audioElements.delete(participant.sid);
      }
    }
  }

  function handleParticipantDisconnected(participant: RemoteParticipant) {
    const audioElement = audioElements.get(participant.sid);
    if (audioElement) {
      audioElement.srcObject = null;
      audioElement.remove();
      audioElements.delete(participant.sid);
    }
  }

  onMount(async () => {
    try {
      // Fetch token from your SvelteKit API endpoint
      const tokenResponse = await fetch("/api/getToken");
      token = await tokenResponse.json();

      const coreMemoryResponse = await fetch("api/getMemory");
      memory = await coreMemoryResponse.json();
      console.log(memory);
      const coreMemory = memory?.core;
      console.log(coreMemory);

      room = new Room();
      if (!token) {
        console.error("Failed to fetch token");
        return;
      }
      if (!token.wsURL) {
        console.error("Missing LiveKit URL");
        return;
      }

      room.on(RoomEvent.TrackSubscribed, handleTrackSubscribed);
      room.on(RoomEvent.TrackUnsubscribed, handleTrackUnsubscribed);
      room.on(RoomEvent.ParticipantDisconnected, handleParticipantDisconnected);
      room.on(RoomEvent.ConnectionStateChanged, (state: ConnectionState) => {
        connected = state === ConnectionState.Connected;
      });
      room.on(RoomEvent.TranscriptionReceived, handleTranscriptionReceived);

      room.prepareConnection(token.wsURL, token.value);
    } catch (error) {
      console.error("Failed to connect to room:", error);
    }
  });

  onDestroy(() => {
    if (room) {
      room.off(RoomEvent.TrackSubscribed, handleTrackSubscribed);
      room.off(RoomEvent.TrackUnsubscribed, handleTrackUnsubscribed);
      room.off(
        RoomEvent.ParticipantDisconnected,
        handleParticipantDisconnected
      );
      room.off(RoomEvent.TranscriptionReceived, handleTranscriptionReceived);
      room.disconnect();
    }

    // Clean up any remaining audio elements
    audioElements.forEach((element) => {
      element.srcObject = null;
      element.remove();
    });
    audioElements.clear();
  });
</script>

<div class="p-4 w-full">
  <div
    class="flex flex-wrap justify-center max-w-[800px] mx-auto rounded-lg card items-center h-full w-full border border-gray-200 p-15 bg-gray-50"
  >
    <div class="flex items-center space-x-4 justify-center flex-wrap">
      <div
        class="w-[300px] h-[300px] flex justify-center items-center"
        id="button-container"
      >
        <button
          class={`letta-ball relative
         ${buttonShouldBounce ? "shake-vertical bg-gray-200 hover:bg-white" : ""}`}
          aria-label={connected
            ? "Disconnect from conversation"
            : "Connect to conversation"}
          disabled={!connected && (!token || !token.wsURL)}
          on:click={async () => {
            if (connected) {
              await room.disconnect();

              setTimeout(() => {
                showGlow = false;
              }, 500);
              buttonShouldBounce = true;
              console.log("Disconnected from room", buttonShouldBounce);
            } else {
              try {
                await tick();

                await room.connect(token!.wsURL, token!.value);
                console.log("Connected to room", room.name);
                await room.localParticipant.enableCameraAndMicrophone();

                buttonShouldBounce = false;
                showGlow = true;
              } catch (error) {
                console.error("Failed to connect to room:", error);
              }
            }
          }}
        >
          <div class="w-30 h-30 p-5">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 41 40"
              fill="none"
            >
              <path
                d="M24.1831 16.0007H16.1225V24.0004H24.1831V16.0007Z"
                fill="hsl(210, 8%, 80%)"
              ></path>
              <path
                d="M32.2436 5.44985V0H8.06062V5.44985C8.06062 6.8587 6.91086 7.99978 5.4913 7.99978H0V32.0002H5.4913C6.91086 32.0002 8.06062 33.1413 8.06062 34.5502V40H32.2436V34.5502C32.2436 33.1413 33.3934 32.0002 34.8129 32.0002H40.3042V7.99978H34.8129C33.3934 7.99978 32.2436 6.8587 32.2436 5.44985ZM32.2436 29.4492C32.2436 30.858 31.0939 31.9991 29.6743 31.9991H10.6311C9.2115 31.9991 8.06174 30.858 8.06174 29.4492V10.5497C8.06174 9.14086 9.2115 7.99978 10.6311 7.99978H29.6743C31.0939 7.99978 32.2436 9.14086 32.2436 10.5497V29.4492Z"
                fill="hsl(210, 8%, 80%)"
              ></path>
            </svg>
          </div>
        </button>
        {#if showGlow}
          <div
            class={`${connected ? "glowy-ball-shadow" : ""} rounded-full`}
          ></div>
        {/if}
      </div>
      <div
        class="flex-1 overflow-y-auto max-h-80 min-w-[300px] max-w-[400px] ml-5 text-gray-500"
        id="transcription-container"
      >
        {#if Object.keys(transcriptions).length === 0}
          <div>
            Welcome to the Letta Voice demo. Tap on the orb to connect, then
            speak to see transcriptions appear here.
          </div>
        {/if}
        <ul>
          {#each Object.values(transcriptions).sort((a, b) => a.firstReceivedTime - b.firstReceivedTime) as segment, index (segment.id)}
            <li
              class={index === Object.values(transcriptions).length - 1
                ? "font-bold text-black"
                : "text-gray-300"}
            >
              {segment.text}
            </li>
          {/each}
        </ul>
      </div>
    </div>
  </div>
  <div class="flex items-center justify-center" id="memory-container">
    <div class="flex flex-col w-full max-w-[800px]">
      <button
        class="flex items-center space-x-2 mb-2 text-gray-600 hover:text-gray-900 focus:outline-none"
        on:click={() => (isMemoryExpanded = !isMemoryExpanded)}
        aria-expanded={isMemoryExpanded}
      >
        <svg
          class="w-5 h-5 transition-transform duration-300"
          class:rotate-180={isMemoryExpanded}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M19 9l-7 7-7-7"
          />
        </svg>
        <h3 class="text-md font-medium">
          {isMemoryExpanded ? "Hide" : "Show"} Memory
        </h3>
      </button>
      {#if memory}
        {#if isMemoryExpanded}
          <div
            transition:slide={{ duration: 500 }}
            class="p-4 rounded-lg bg-gray-50 overflow-hidden card"
          >
            <h4 class="text-sm font-medium uppercase mb-2">Core Memory</h4>
            {#each memory.core as item}
              <div class="text-sm text-gray-700">
                {#each Object.entries(item || {}) as [key, value]}
                  <div class="py-2">
                    <strong>{key}</strong>
                  </div>
                  <div class="flex">
                    <div class="w-1 bg-gray-300 mr-2"></div>
                    <span class="whitespace-pre-line">{value}</span>
                  </div>
                {/each}
              </div>
            {/each}

            <h4 class="text-sm font-medium uppercase mb-2 pt-8">
              Archival Memory
            </h4>
            {#each memory.archival as item}
              {#each Object.entries(item || {}) as [key, value]}
                <div>
                  <strong>{key}</strong>:
                  <span class="whitespace-pre-line">{value}</span>
                </div>
              {/each}
            {/each}
          </div>
        {/if}
      {:else}
        <div class="text-gray-500">Loading memory...</div>
      {/if}
    </div>
  </div>
</div>

<style lang="postcss">
  @reference "tailwindcss";
</style>
