import streamlit as st
from haystack import Pipeline
from haystack.document_stores import FAISSDocumentStore
from haystack.nodes import Shaper, PromptNode, PromptTemplate, PromptModel, EmbeddingRetriever
from haystack.nodes.retriever.web import WebRetriever


@st.cache_resource(show_spinner=False)
def get_plain_pipeline():
    prompt_open_ai = PromptModel(model_name_or_path="text-davinci-003", api_key=st.secrets["OPENAI_API_KEY"])
    # Now let make one PromptNode use the default model and the other one the OpenAI model:
    plain_llm_template = PromptTemplate(name="plain_llm", prompt_text="Answer the following question: $query")
    node_openai = PromptNode(prompt_open_ai, default_prompt_template=plain_llm_template, max_length=300)
    pipeline = Pipeline()
    pipeline.add_node(component=node_openai, name="prompt_node", inputs=["Query"])
    return pipeline


@st.cache_resource(show_spinner=False)
def get_retrieval_augmented_pipeline():
    ds = FAISSDocumentStore(faiss_index_path="data/my_faiss_index.faiss",
                            faiss_config_path="data/my_faiss_index.json")

    retriever = EmbeddingRetriever(
        document_store=ds,
        embedding_model="sentence-transformers/multi-qa-mpnet-base-dot-v1",
        model_format="sentence_transformers",
        top_k=2
    )
    shaper = Shaper(func="join_documents", inputs={"documents": "documents"}, outputs=["documents"])

    default_template = PromptTemplate(
        name="question-answering",
        prompt_text="Given the context please answer the question. Context: $documents; Question: "
                    "$query; Answer:",
    )
    # Let's initiate the PromptNode
    node = PromptNode("text-davinci-003", default_prompt_template=default_template,
                      api_key=st.secrets["OPENAI_API_KEY"], max_length=500)

    # Let's create a pipeline with Shaper and PromptNode
    pipeline = Pipeline()
    pipeline.add_node(component=retriever, name='retriever', inputs=['Query'])
    pipeline.add_node(component=shaper, name="shaper", inputs=["retriever"])
    pipeline.add_node(component=node, name="prompt_node", inputs=["shaper"])
    return pipeline


@st.cache_resource(show_spinner=False)
def get_web_retrieval_augmented_pipeline():
    search_key = st.secrets["WEBRET_API_KEY"]
    web_retriever = WebRetriever(api_key=search_key, search_engine_provider="SerperDev")
    shaper = Shaper(func="join_documents", inputs={"documents": "documents"}, outputs=["documents"])
    default_template = PromptTemplate(
        name="question-answering",
        prompt_text="Given the context please answer the question. Context: $documents; Question: "
                    "$query; Answer:",
    )
    # Let's initiate the PromptNode
    node = PromptNode("text-davinci-003", default_prompt_template=default_template,
                      api_key=st.secrets["OPENAI_API_KEY"], max_length=500)
    # Let's create a pipeline with Shaper and PromptNode
    pipeline = Pipeline()
    pipeline.add_node(component=web_retriever, name='retriever', inputs=['Query'])
    pipeline.add_node(component=shaper, name="shaper", inputs=["retriever"])
    pipeline.add_node(component=node, name="prompt_node", inputs=["shaper"])
    return pipeline