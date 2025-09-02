import os
import json
import asyncio
import nest_asyncio
from typing import Optional, TypedDict, Dict
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from openai import OpenAI


nest_asyncio.apply()


class ToolDefinition(TypedDict):
    name: str
    description: str
    parameters: dict


class MCPClient:
    def __init__(self):
        self.sessions: Optional[ClientSession] = []
        self.exit_stack = AsyncExitStack()
        self.deepseek = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com/v1")
        self.available_tools: list[ToolDefinition] = []
        self.tool_to_session: Dict[str, ClientSession] = {}

    async def _send_message(self, messages: list, tools: list) -> str:
        response = self.deepseek.chat.completions.create(model="deepseek-chat", messages=messages, tools=tools)
        return response.choices[0].message

    async def connect_to_server(self, server_name: str, server_config: dict) -> None:
        """
        Connect to an MCP server
        """
        try:
            server_params = StdioServerParameters(**server_config)
            stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
            read, write = stdio_transport
            session = await self.exit_stack.enter_async_context(ClientSession(read, write))

            await session.initialize()
            self.sessions.append(session)

            # List available tools
            response = await session.list_tools()
            tools = response.tools
            print("\nConnected to server with tools:", [tool.name for tool in tools])

            for tool in tools:
                self.tool_to_session[tool.name] = session
                self.available_tools.append(
                    {
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": tool.inputSchema,
                        },
                    }
                )
        except Exception as e:
            print(f"Failed to connect to {server_name}: {e}")

    async def connect_to_servers(self):
        """
        Connect to all configured MCP servers.
        """
        try:
            with open("servers_config.json", "r") as f:
                data = json.load(f)

            servers = data.get("mcpServers", {})

            for server_name, server_config in servers.items():
                await self.connect_to_server(server_name, server_config)
        except Exception as e:
            print(f"Error loading server configuration: {e}")
            raise

    async def process_query(self, query: str) -> str:
        """Process a query using Claude and available tools"""
        messages = [{"role": "user", "content": query}]
        final_text = []

        response = await self._send_message(messages=messages, tools=self.available_tools)
        messages.append(response)

        # Process response and handle tool calls
        # 循环调用工具
        epoch = 0
        while response.tool_calls and epoch < 5:
            tool = response.tool_calls[0]
            tool_name = tool.function.name
            tool_args = tool.function.arguments

            # Call a tool
            session = self.tool_to_session[tool_name]
            tool_call_result = await session.call_tool(tool_name, json.loads(tool_args))
            # final_text.append(f"[Calling tool {tool_name}]")

            messages.append({"role": "tool", "tool_call_id": tool.id, "content": tool_call_result.content[0].text})
            response = await self._send_message(messages, self.available_tools)
            messages.append(response)

        if epoch >= 5:
            final_text.append("[Max tool call limit reached]")
        else:
            final_text.append(response.content)

        return "\n".join(final_text)

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() == 'quit':
                    break

                response = await self.process_query(query)
                print("\n" + response)

            except Exception as e:
                print(f"\nError: {str(e)}")

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()


async def main():
    client = MCPClient()
    try:
        await client.connect_to_servers()
        await client.chat_loop()
    finally:
        await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
