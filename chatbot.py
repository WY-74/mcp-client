import os
import json
import asyncio
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from openai import OpenAI


class MCPClient:
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.deepseek = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com/v1")

    async def _send_message(self, messages: list, tools: list) -> str:
        response = self.deepseek.chat.completions.create(model="deepseek-chat", messages=messages, tools=tools)
        return response.choices[0].message

    async def connect_to_server(self):
        """
        Connect to an MCP server
        """
        server_params = StdioServerParameters(command="uv", args=["run", "servers/server_arxiv.py"], env=None)

        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        read, write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(read, write))

        await self.session.initialize()

        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])

    async def process_query(self, query: str) -> str:
        """Process a query using Claude and available tools"""
        messages = [{"role": "user", "content": query}]
        final_text = []

        response = await self.session.list_tools()
        available_tools = [
            {
                "type": "function",
                "function": {"name": tool.name, "description": tool.description, "parameters": tool.inputSchema},
            }
            for tool in response.tools
        ]

        response = await self._send_message(messages=messages, tools=available_tools)
        messages.append(response)

        # Process response and handle tool calls
        if not response.tool_calls:
            final_text.append(response.content)
        else:
            tool = response.tool_calls[0]
            tool_name = tool.function.name
            tool_args = tool.function.arguments

            tool_call_result = await self.session.call_tool(tool_name, json.loads(tool_args))
            final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

            messages.append({"role": "tool", "tool_call_id": tool.id, "content": tool_call_result.content[0].text})
            response = await self._send_message(messages, available_tools)
            messages.append(response)

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
        await client.connect_to_server()
        await client.chat_loop()
    finally:
        await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
