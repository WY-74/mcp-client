import os
import asyncio
import json
from typing import Optional, Dict
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from openai import OpenAI

from conversations import Conversations


class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.deepseek = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com/v1")
        self.exit_stack = AsyncExitStack()
        self.client_session: Optional[ClientSession] = None
        self.conversations = Conversations()

    def _handle_new_command(self, context_id: str):
        parts = context_id.split(' ', 1)
        if len(parts) == 2:
            _, context_id = parts
            self.conversations.create_context(context_id)
            print(f"Created context: {context_id}")

    def _handle_switch_command(self, context_id: str):
        parts = context_id.split(' ', 1)
        if len(parts) == 2:
            _, context_id = parts
            self.conversations.switch_context(context_id)
            print(f"Switched to context: {context_id}")

    async def _send_message(self, messages: list, tools: list) -> str:
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
        self.client_session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        await self.client_session.initialize()
        self.conversations.create_context("default")

        response = await self.client_session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])

    async def chat_loop(self):
        print("\nMCP Client Started!")
        print("Commands:")
        print("- 'new <context_id>' - Create new conversation context")
        print("- 'switch <context_id>' - Switch to context")
        print("- 'quit' - Exit")
        print("- Or just type your query for current context")

        while True:
            try:
                query = input("Query: ").strip()

                if query.lower() == 'quit':
                    break
                elif query.startswith('new '):
                    self._handle_new_command(query)
                elif query.startswith('switch '):
                    self._handle_switch_command(query)
                else:
                    response = await self.process_query(query)
                    print("\nResponse: ", response)

            except Exception as e:
                print(f"\nError: {str(e)}")

    async def process_query(self, query: str) -> str:
        context = self.conversations.get_current_context()
        if not context:
            return "No active context"

        final_text = []
        context.add_message({"role": "user", "content": query})

        tools = await self.client_session.list_tools()
        available_tools = [
            {
                "type": "function",
                "function": {"name": tool.name, "description": tool.description, "parameters": tool.inputSchema},
            }
            for tool in tools.tools
        ]

        response = await self._send_message(context.get_messages(), available_tools)
        context.add_message(response)

        if not response.tool_calls:
            final_text.append(response.content)
        else:
            tool = response.tool_calls[0]
            tool_name = tool.function.name
            tool_args = tool.function.arguments

            tool_call_result = await self.client_session.call_tool(tool_name, json.loads(tool_args))
            final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

            # assistant_message_content.append(response)
            context.add_message({"role": "tool", "tool_call_id": tool.id, "content": tool_call_result.content[0].text})

            response = await self._send_message(context.get_messages(), available_tools)
            context.add_message(response)

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
