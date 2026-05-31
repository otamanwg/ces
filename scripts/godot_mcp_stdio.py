import asyncio
import json
import sys
import threading
import urllib.error
import urllib.request

import websockets

from godot_mcp_bridge import Bridge


TOOL_NAMES = [
    "list_dir",
    "read_file",
    "search_project",
    "create_script",
    "create_scene",
    "read_scene",
    "add_node",
    "remove_node",
    "modify_node_property",
    "rename_node",
    "move_node",
    "attach_script",
    "detach_script",
    "set_collision_shape",
    "set_sprite_texture",
    "get_scene_hierarchy",
    "get_scene_node_properties",
    "set_scene_node_property",
    "edit_script",
    "validate_script",
    "list_scripts",
    "create_folder",
    "delete_file",
    "rename_file",
    "get_project_settings",
    "list_settings",
    "update_project_settings",
    "get_input_map",
    "configure_input_map",
    "get_collision_layers",
    "setup_autoload",
    "get_node_properties",
    "get_console_log",
    "get_errors",
    "clear_console_log",
    "open_in_godot",
    "scene_tree_dump",
    "classdb_query",
    "rescan_filesystem",
    "run_scene",
    "stop_scene",
    "is_playing",
    "generate_2d_asset",
    "map_project",
    "map_scenes",
]


def log(message: str) -> None:
    print(f"[godot-mcp-stdio] {message}", file=sys.stderr, flush=True)


class StdioGodotMcp:
    def __init__(self) -> None:
        self.bridge = Bridge()
        self.loop = asyncio.new_event_loop()
        self.owns_websocket = False
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        self._start_websocket_or_proxy()

    def _run_loop(self) -> None:
        asyncio.set_event_loop(self.loop)
        self.bridge.loop = self.loop
        self.loop.run_forever()

    def _start_websocket_or_proxy(self) -> None:
        future = asyncio.run_coroutine_threadsafe(self._start_websocket(), self.loop)
        try:
            future.result(timeout=3)
            self.owns_websocket = True
            log("listening on ws://127.0.0.1:6505")
        except Exception as exc:
            self.owns_websocket = False
            log(f"using existing bridge/proxy instead of 6505 listener: {exc}")

    async def _start_websocket(self) -> None:
        server = await websockets.serve(self.bridge.on_godot, "127.0.0.1", 6505)
        self._server = server

    def invoke(self, tool: str, args: dict, timeout: float = 30) -> dict:
        if self.owns_websocket:
            future = asyncio.run_coroutine_threadsafe(
                self.bridge.invoke(tool, args, timeout),
                self.loop,
            )
            return future.result(timeout + 2)

        return self._invoke_existing_bridge(tool, args, timeout)

    def _invoke_existing_bridge(self, tool: str, args: dict, timeout: float) -> dict:
        body = json.dumps({
            "tool": tool,
            "args": args,
            "timeout": timeout,
        }).encode("utf-8")
        request = urllib.request.Request(
            "http://127.0.0.1:6507/invoke",
            data=body,
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout + 2) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            payload = exc.read().decode("utf-8")
            try:
                return json.loads(payload)
            except json.JSONDecodeError:
                return {"ok": False, "success": False, "error": payload or str(exc)}


def send(payload: dict) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def tool_definition(name: str) -> dict:
    return {
        "name": name,
        "description": f"Invoke Godot editor MCP tool '{name}' through the running Godot MCP plugin.",
        "inputSchema": {
            "type": "object",
            "additionalProperties": True,
        },
    }


def handle_request(server: StdioGodotMcp, request: dict) -> dict | None:
    request_id = request.get("id")
    method = request.get("method")
    params = request.get("params") or {}

    if request_id is None:
        return None

    try:
        if method == "initialize":
            result = {
                "protocolVersion": params.get("protocolVersion", "2024-11-05"),
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "city-game-godot-mcp",
                    "version": "0.1.0",
                },
            }
        elif method == "tools/list":
            result = {"tools": [tool_definition(name) for name in TOOL_NAMES]}
        elif method == "tools/call":
            tool = params.get("name")
            args = params.get("arguments") or {}
            if tool not in TOOL_NAMES:
                raise ValueError(f"Unknown Godot MCP tool: {tool}")
            if not isinstance(args, dict):
                raise ValueError("Tool arguments must be an object")
            raw_result = server.invoke(tool, args)
            is_error = not bool(raw_result.get("success", raw_result.get("ok", False)))
            result = {
                "content": [{
                    "type": "text",
                    "text": json.dumps(raw_result, ensure_ascii=False, indent=2),
                }],
                "isError": is_error,
            }
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            }

        return {"jsonrpc": "2.0", "id": request_id, "result": result}
    except Exception as exc:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32000, "message": str(exc)},
        }


def main() -> None:
    server = StdioGodotMcp()
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError as exc:
            log(f"invalid JSON-RPC message: {exc}")
            continue
        response = handle_request(server, request)
        if response is not None:
            send(response)


if __name__ == "__main__":
    main()
