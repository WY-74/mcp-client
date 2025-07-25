import os
import asyncio
import json
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from openai import OpenAI


class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.deepseek = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com/v1")
        self.session_messages = []

    async def send_message(self, messages: list, tools: list) -> str:
        response = self.deepseek.chat.completions.create(model="deepseek-chat", messages=messages, tools=tools)
        return response.choices[0].message

    async def connect_to_server(self, server_script_path: str):
        """Connect to an MCP server

        Args:
            server_script_path: Path to the server script (.py or .js)
        """
        is_python = server_script_path.endswith('.py')
        is_js = server_script_path.endswith('.js')
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")

        command = "python" if is_python else "node"
        server_params = StdioServerParameters(command=command, args=[server_script_path], env=None)

        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        await self.session.initialize()

        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])

    async def chat_loop(self):
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input("Query: ").strip()

                if query.lower() == 'quit':
                    break

                response = await self.process_query(query)
                print("\nResponse: ", response)

            except Exception as e:
                print(f"\nError: {str(e)}")

    async def process_query(self, query: str) -> str:
        final_text = []
        # assistant_message_content = []

        self.session_messages.append({"role": "user", "content": query})

        # messages = [{"role": "user", "content": query}]
        tools = await self.session.list_tools()
        available_tools = [
            {
                "type": "function",
                "function": {"name": tool.name, "description": tool.description, "parameters": tool.inputSchema},
            }
            for tool in tools.tools
        ]

        response = await self.send_message(self.session_messages, available_tools)

        if not response.tool_calls:
            final_text.append(response.content)
            self.session_messages.append(response)
            # assistant_message_content.append(response)
        else:
            for tool_call in response.tool_calls:
                tool_name = tool_call.function.name
                tool_args = tool_call.function.arguments

                tool_call_result = await self.session.call_tool(tool_name, json.loads(tool_args))
                final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

                # assistant_message_content.append(response)
                self.session_messages.append(response)
                self.session_messages.append(
                    {"role": "tool", "tool_call_id": tool_call.id, "content": tool_call_result.content[0].text}
                )

                response = await self.send_message(self.session_messages, available_tools)

                final_text.append(response.content)

        return "\n".join(final_text)

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()


async def main():
    if len(sys.argv) != 2:
        print("Usage: python client.py <server_script_path>")
        sys.exit(1)

    client = MCPClient()
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()


if __name__ == "__main__":
    import sys

    asyncio.run(main())
