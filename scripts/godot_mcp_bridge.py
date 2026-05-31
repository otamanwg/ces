import argparse
import asyncio
import json
import sys
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import websockets


class Bridge:
    def __init__(self) -> None:
        self.loop: asyncio.AbstractEventLoop | None = None
        self.godot = None
        self.pending: dict[str, asyncio.Future] = {}
        self.project_path = ""

    async def on_godot(self, websocket) -> None:
        self.godot = websocket
        print("Godot connected", flush=True)
        try:
            async for raw in websocket:
                await self._handle_message(raw)
        finally:
            if self.godot is websocket:
                self.godot = None
            for future in self.pending.values():
                if not future.done():
                    future.set_exception(RuntimeError("Godot disconnected"))
            self.pending.clear()
            print("Godot disconnected", flush=True)

    async def _handle_message(self, raw: str) -> None:
        try:
            message = json.loads(raw)
        except json.JSONDecodeError:
            print(f"Invalid JSON from Godot: {raw}", file=sys.stderr, flush=True)
            return

        msg_type = message.get("type")
        if msg_type == "godot_ready":
            self.project_path = message.get("project_path", "")
            print(f"Godot ready: {self.project_path}", flush=True)
            return

        if msg_type == "tool_result":
            request_id = message.get("id", "")
            future = self.pending.pop(request_id, None)
            if future and not future.done():
                future.set_result(message)
            return

        if msg_type == "pong":
            return

        print(f"Message from Godot: {message}", flush=True)

    async def invoke(self, tool: str, args: dict, timeout: float) -> dict:
        if self.godot is None:
            raise RuntimeError("Godot is not connected")

        request_id = str(uuid.uuid4())
        future = self.loop.create_future()
        self.pending[request_id] = future
        payload = {
            "type": "tool_invoke",
            "id": request_id,
            "tool": tool,
            "args": args,
        }
        await self.godot.send(json.dumps(payload))
        try:
            return await asyncio.wait_for(future, timeout)
        finally:
            self.pending.pop(request_id, None)

    def status(self) -> dict:
        return {
            "godot_connected": self.godot is not None,
            "project_path": self.project_path,
            "pending": len(self.pending),
        }


class ControlHandler(BaseHTTPRequestHandler):
    server_version = "GodotMcpBridge/0.1"

    def _send_json(self, status: int, payload: dict) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        if self.path != "/status":
            self._send_json(404, {"ok": False, "error": "Not found"})
            return
        self._send_json(200, {"ok": True, **self.server.bridge.status()})

    def do_POST(self) -> None:
        if self.path != "/invoke":
            self._send_json(404, {"ok": False, "error": "Not found"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length).decode("utf-8")
            request = json.loads(body) if body else {}
            tool = str(request["tool"])
            args = request.get("args", {})
            timeout = float(request.get("timeout", 30))
            if not isinstance(args, dict):
                raise ValueError("'args' must be an object")
        except Exception as exc:
            self._send_json(400, {"ok": False, "error": str(exc)})
            return

        try:
            future = asyncio.run_coroutine_threadsafe(
                self.server.bridge.invoke(tool, args, timeout),
                self.server.bridge.loop,
            )
            result = future.result(timeout + 2)
            status = 200 if result.get("success", False) else 500
            self._send_json(status, {"ok": result.get("success", False), **result})
        except Exception as exc:
            self._send_json(503, {"ok": False, "error": str(exc)})

    def log_message(self, fmt: str, *args) -> None:
        print("HTTP " + (fmt % args), flush=True)


def start_control_server(bridge: Bridge, host: str, port: int) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer((host, port), ControlHandler)
    server.bridge = bridge
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ws-host", default="127.0.0.1")
    parser.add_argument("--ws-port", type=int, default=6505)
    parser.add_argument("--http-host", default="127.0.0.1")
    parser.add_argument("--http-port", type=int, default=6507)
    args = parser.parse_args()

    bridge = Bridge()
    bridge.loop = asyncio.get_running_loop()
    control = start_control_server(bridge, args.http_host, args.http_port)
    print(f"HTTP control listening on http://{args.http_host}:{args.http_port}", flush=True)

    async with websockets.serve(bridge.on_godot, args.ws_host, args.ws_port):
        print(f"Godot WebSocket listening on ws://{args.ws_host}:{args.ws_port}", flush=True)
        try:
            await asyncio.Future()
        finally:
            control.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
