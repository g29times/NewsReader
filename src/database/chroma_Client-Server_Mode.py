# 1 Terminal 启动数据库
# chroma run --path /db_path
# eg. chroma run --path /voyager-backend/db

# https://docs.trychroma.com/production/chroma-server/client-server-mode
# 2 连接数据库
import chromadb
chroma_client = chromadb.HttpClient(host='localhost', port=8000)
collection = chroma_client.get_or_create_collection(name="news_reader_articles")
# collection.upsert(
#     documents=["hello world"],
#     ids=["id1"]
#     # ids=["id1", "id2", "id3"],
#     # metadatas=[{"chapter": "3", "verse": "16"}, {"chapter": "3", "verse": "5"}, {"chapter": "29", "verse": "11"}],
#     # documents=["doc1", "doc2", "doc3"],
# )
print(collection.get(
    ids=["article_90_chunk_3","article_90_chunk_4"],
	# where={"style": "style1"}
))
# collection.query(
#     n_results=10,
#     where={"metadata_field": "is_equal_to_this"},
#     where_document={"$contains":"search_string"}
# )
# collection.delete(
#     ids=["id1", "id2", "id3",...],
# 	where={"chapter": "20"}
# )

# 3 异步方式
import asyncio
import chromadb
async def main():
    client = await chromadb.AsyncHttpClient()
    collection = await client.get_or_create_collection(name="test_async")
    await collection.add(
        documents=["hello world"],
        ids=["id1"]
    )
    print(await collection.get(
        ids=["id1"]
    ))
asyncio.run(main())
