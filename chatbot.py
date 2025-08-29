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
        self.available_tools: List[dict] = []

    async def process_query(self, query):
        messages = [{"role": "user", "content": query}]
        response = self.deepseek.messages.create(
            max_tokens=1024,
            model="deepseek-chat",
            messages=messages,
            tools=self.available_tools
        )

        print(response)

        # 开始多轮对话
        # while True:
        #     assistant_content = []
        #     for content in response.choices[0].message:
        #         pass


        # return response.choices[0].message.content

if __name__ == "__main__":
    bot = ChatBot()
    asyncio.run(bot.process_query("Hello, how can I help you today?"))

