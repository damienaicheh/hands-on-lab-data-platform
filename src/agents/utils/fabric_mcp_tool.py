from agent_framework import MCPStreamableHTTPTool


class FabricDataAgentMCPTool(MCPStreamableHTTPTool):
    """MCP tool for a published Fabric data agent exposed over streamable HTTP.

    The Fabric data agent MCP server does not implement the JSON-RPC ``ping``
    method. Instead of returning a ``-32601`` (method not found) error that the
    framework handles gracefully, it responds with an HTTP ``400 Bad Request``,
    which tears down the streamable HTTP transport and surfaces as a
    ``CancelledError`` during connection setup and before every tool call.

    This subclass skips the proactive ``ping`` health-check performed by
    ``_ensure_connected``. The regular ``call_tool`` path keeps its own
    reconnect-and-retry logic, so connection resilience is preserved.
    """

    async def _ensure_connected(self) -> None:  # noqa: RUF029
        return
