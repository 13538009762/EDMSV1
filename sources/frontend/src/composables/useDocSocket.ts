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

  // 1. 定义监听函数
  const onYjsUpdate = (msg: { document_id?: number; payload?: string }) => {
    if (msg.document_id === roomId && msg.payload) {
      try { Y.applyUpdate(ydoc, fromB64(msg.payload), "remote"); } catch { /* ignore */ }
    }
  };

  const onAwarenessUpdate = (msg: { document_id?: number; payload?: string }) => {
    if (msg.document_id === roomId && msg.payload) {
      try { applyAwarenessUpdate(awareness, fromB64(msg.payload), "remote"); } catch { /* ignore */ }
    }
  };

  const onStatusChange = (data: any) => {
    if (data.document_id === roomId) {
       window.dispatchEvent(new CustomEvent("edms:status_changed", { detail: data }));
    }
  };

  // 2. 绑定 Socket 监听
  socket.on("connect", () => socket.emit("join_document", { document_id: roomId }));
  socket.on("yjs_update", onYjsUpdate);
  socket.on("awareness_update", onAwarenessUpdate);
  socket.on("status_change", onStatusChange);

  // 3. 绑定 Yjs/Awareness 本地监听
  const onDocUpdate = (update: Uint8Array, origin: unknown) => {
    if (origin === "remote") return;
    socket.emit("yjs_update", { document_id: roomId, payload: toB64(update) });
  };
  ydoc.on("update", onDocUpdate);

  const onLocalAwareUpdate = (
    changes: { added: number[]; updated: number[]; removed: number[] },
    origin: unknown,
  ) => {
    if (origin === "remote") return;
    const { added, updated, removed } = changes;
    const clients = [...added, ...updated, ...removed];
    const up = encodeAwarenessUpdate(awareness, clients);
    socket.emit("awareness_update", { document_id: roomId, payload: toB64(up) });
  };
  awareness.on("update", onLocalAwareUpdate);

  // 4. 设置初始状态
  awareness.setLocalStateField("user", { name: user.name, color: user.color });

  // 5. 极简注销逻辑
  return () => {
    // 停止所有监听
    ydoc.off("update", onDocUpdate);
    awareness.off("update", onLocalAwareUpdate);
    socket.off("yjs_update", onYjsUpdate);
    socket.off("awareness_update", onAwarenessUpdate);
    socket.off("status_change", onStatusChange);
    
    // 通知离线并关闭
    socket.emit("leave_document", { document_id: roomId });
    socket.disconnect();
  };
}
