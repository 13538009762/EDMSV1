import * as Y from "yjs";
import {
  applyAwarenessUpdate,
  encodeAwarenessUpdate,
} from "y-protocols/awareness";
import type { Awareness } from "y-protocols/awareness";
import { io, Socket } from "socket.io-client";

function toB64(u8: Uint8Array): string {
  let s = "";
  for (let i = 0; i < u8.length; i++) s += String.fromCharCode(u8[i]!);
  return btoa(s);
}

function fromB64(b64: string): Uint8Array {
  const s = atob(b64);
  const u = new Uint8Array(s.length);
  for (let i = 0; i < s.length; i++) u[i] = s.charCodeAt(i);
  return u;
}

export function attachDocCollab(
  documentId: number,
  ydoc: Y.Doc,
  awareness: Awareness,
  user: { name: string; color: string },
): () => void {
  const url = import.meta.env.VITE_SOCKET_URL || "";
  const socket: Socket = io(url || undefined, {
    path: "/socket.io",
    transports: ["websocket", "polling"],
  });

  const roomId = documentId;

  function onYjs(msg: { document_id?: number; payload?: string }) {
    if (msg.document_id !== roomId || !msg.payload) return;
    try {
      Y.applyUpdate(ydoc, fromB64(msg.payload), "remote");
    } catch {
      /* ignore */
    }
  }

  function onAware(msg: { document_id?: number; payload?: string }) {
    if (msg.document_id !== roomId || !msg.payload) return;
    try {
      applyAwarenessUpdate(awareness, fromB64(msg.payload), "remote");
    } catch {
      /* ignore */
    }
  }

  socket.on("connect", () => {
    socket.emit("join_document", { document_id: roomId });
  });
  socket.on("yjs_update", onYjs);
  socket.on("awareness_update", onAware);

  const onDocUpdate = (update: Uint8Array, origin: unknown) => {
    if (origin === "remote") return;
    socket.emit("yjs_update", { document_id: roomId, payload: toB64(update) });
  };
  ydoc.on("update", onDocUpdate);

  const onAwareUpdate = (
    changes: { added: number[]; updated: number[]; removed: number[] },
    origin: unknown,
  ) => {
    if (origin === "remote") return;
    const { added, updated, removed } = changes;
    const clients = [...added, ...updated, ...removed];
    const up = encodeAwarenessUpdate(awareness, clients);
    socket.emit("awareness_update", { document_id: roomId, payload: toB64(up) });
  };
  awareness.on("update", onAwareUpdate);

  awareness.setLocalStateField("user", { name: user.name, color: user.color });

  function disconnect() {
    ydoc.off("update", onDocUpdate);
    awareness.off("update", onAwareUpdate);
    socket.off("yjs_update", onYjs);
    socket.off("awareness_update", onAware);
    socket.emit("leave_document", { document_id: roomId });
    socket.close();
  }

  return disconnect;
}
