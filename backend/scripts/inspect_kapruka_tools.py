import anyio
import sys
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


MCP_URL = "https://mcp.kapruka.com/mcp"
sys.stdout.reconfigure(encoding="utf-8")


async def main() -> None:
    async with streamablehttp_client(MCP_URL) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools = await session.list_tools()

            for tool in tools.tools:
                print(f"{tool.name}: {tool.description}")


if __name__ == "__main__":
    anyio.run(main)
