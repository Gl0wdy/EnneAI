import asyncio
from enneai.ai.rag.query import retrieve, warmup

async def main():
    await warmup()
    while True:
        query = input("Enter your query: ")
        context = await retrieve(query, rerank_top_n=25)
        print(f"{context.text}\n") 
        print("==================\n")   

if __name__ == "__main__":
    asyncio.run(main())