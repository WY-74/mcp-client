import asyncio
import nest_asyncio
from typing import List
from anthropic import Anthropic
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client


server_params = StdioServerParameters(
    command = "uv",
    args = ["run", "servers/server_arxiv.py"],
    env=None
)

class ChatBot:
    def __init__(self):
        self.session: ClientSession = None
        self.deepseek: Anthropic = Anthropic()
        self.available_tools: List[dict]|None = None

    async def process_query(self, query):
        messages = [{"role": "user", "content": query}]
        response = self.deepseek.messages.create(
            max_tokens=1024,
            model="deepseek-chat",
            messages=messages,
            tools=self.available_tools
        )

        # 开始多轮对话
        process_query = True
        while process_query:
            assistant_content = []
            for content in response.content:
                if content.type == "text":
                    print(content.text)
                    assistant_content.append(content)
                    if (len(assistant_content) == 1):
                        process_query = False
                elif content.type == "tool_use":
                    assistant_content.append(content)
                    messages.append({"role": "assistant", "content": assistant_content})
                    tool_id = content.id
                    tool_args = content.input
                    tool_name = content.name

                    print(f"Calling tool {tool_name} with args {tool_args}")
                    result = await self.session.call_tool(tool_name, tool_args)

                    messages.append({
                         "role": "user",
                         "content": [
                             {
                                "type": "tool_result",
                                "tool_use_id": tool_id,
                                "content": result.content
                             }
                         ]
                    })

                    response = self.deepseek.messages.create(
                        max_tokens=1024,
                        model="deepseek-chat",
                        messages=messages,
                        tools=self.available_tools
                    )

                    if (len(response.content)) == 1 and response.content[0].type == "text":
                        print(response.content[0].text)
                        process_query = False

    async def chat_loop(self):
        print("\nMCP ChatBot Started!")
        print("Type your queries or 'quit' to exit.")
        
        while True:
            try:
                query = input("\nQuery: ").strip()

                if query == "quit":
                    break
                
                await self.process_query(query)
                print("\n")
            except Exception as e:
                print(f"\nError: {e}")

    async def connect_to_server_and_run(self):
        server_params = StdioServerParameters(
            command = "uv",
            args = ["run", "servers/server_arxiv.py"],
            env=None
        )
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                self.session = session
                await self.session.initialize()

                response = await self.session.list_tools()
                tools = response.tools
                print("\nConnected to server with tools: ", [tool.name for tool in tools])

                self.available_tools = [
                    {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                } for tool in tools
            ]
            
            await self.chat_loop()


async def main():
    bot = ChatBot()
    await bot.connect_to_server_and_run()


if __name__ == "__main__":
    asyncio.run(main())

