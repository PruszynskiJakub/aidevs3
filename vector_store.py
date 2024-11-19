from langchain.schema import Document
from langchain_community.vectorstores import InMemoryVectorStore
from langchain_openai import OpenAIEmbeddings

vector_store = InMemoryVectorStore(OpenAIEmbeddings())


def index_image(image_data):
    document1 = Document(page_content=image_data["desc"], metadata={
        "data": f"{image_data['desc']} - {image_data['name']} - {image_data['url']} - {image_data['context']}"})
    document2 = Document(page_content=image_data["context"], metadata={
        "data": f"{image_data['desc']} - {image_data['name']} - {image_data['url']} - {image_data['context']}"})
    vector_store.add_documents([document1, document2])


def index_audio(audio_data):
    document1 = Document(page_content=audio_data["transcript"], metadata={"data": audio_data})
    document2 = Document(page_content=audio_data["context"], metadata={"data": audio_data})
    vector_store.add_documents([document1, document2])


def index_chunk(chunk_text, metadata={}):
    document = Document(page_content=chunk_text, metadata=metadata)
    vector_store.add_documents([document])


def search(query, limit=10) -> list[Document]:
    return vector_store.search(query=query, search_type="similarity")
