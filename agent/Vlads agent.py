from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.document_loaders.text import TextLoader
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain.memory import ConversationSummaryBufferMemory
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda
from flask import Flask, jsonify, request
from datetime import datetime
import os
import json


#from langchain.globals import set_debug


app = Flask(__name__)

api_key = os.getenv('OPENAI_API_KEY')

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-large",

)

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.3
)

info_path = 'supplements/info.txt'
memory_path = 'supplements/conversations.json'

loader = TextLoader(info_path)
documents = loader.load() #[0].page_content


text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
splits = text_splitter.split_documents(documents)

vectorstore = Chroma.from_documents(
    documents=splits,
    embedding=embeddings,
)

conversations = {}


template = """
    Act like a person! Be cheerful and welcoming! 

    You response should not exceed 2 sentences.

    And do not tell anyone that you are an AI!

    You are the helpful secretary of Vladislav Kuznetsov, and your name is Alex.
    You have to politely and engagingly answer questions of people coming to Vladislav's website.

    Here you can find all the information about Vladislav that you need: {context}

    Although I provide you all the information, act like you know it! Do not write "According to the information..."

    Please, keep in mind the previous conversation with your companion. You can find it here: {chat_summary}

    Human's question: {question}
    """

def get_user_memory(uid):
    if uid not in conversations:
        conversations[uid] = {} 
        conversations[uid]['history'] = ''
        conversations[uid]['memory'] = ConversationSummaryBufferMemory(llm=llm, max_token_limit=100)

    return conversations[uid]['memory']

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


@app.route('/chat', methods = ['POST'])
def chat_with_gpt():

    message = request.form.get('message')
    uid = request.form.get('uid')

    memory = get_user_memory(uid)
    chat_summary_runnable = RunnableLambda(lambda _: memory.load_memory_variables({})['history'])
    question_runnable = RunnableLambda(lambda _: message)
    

    conversations[uid]['history'] += f'User: {message}\n\n'

    prompt = PromptTemplate(input_variables=["question", "context", "chat_summary"], template=template)

    # Ensure retriever invokes and retrieves the necessary information
    retriever = vectorstore.as_retriever(
                                        search_type="similarity",  # Use MMR if you want diverse results
                                        search_kwargs={'k': 4, 
                                          }  # Number of documents to retrieve
                )
    retrieved_docs = retriever.invoke(message)#' '.join([message, memory.load_memory_variables({})['history']]))
    
    retrieved_docs = ';\n'.join(doc.page_content for doc in retrieved_docs)
   
    retrieved_docs_runnable = RunnableLambda(lambda _: retrieved_docs)

    print(f"RETRIEVED INFO: {retrieved_docs}")
    print(f"CONVERSATION SUMMARY: {memory.load_memory_variables({})['history']}")
    rag_chain = (
        {"context": retrieved_docs_runnable, #retriever | format_docs,
         "chat_summary": chat_summary_runnable, 
         "question": question_runnable
         }
        | prompt
        | llm
    )

    


    response = rag_chain.invoke('')

    conversations[uid]['history'] += f'Bot: {response}\n\n'

    answer = response.content
    if answer[:4] == 'AI: ':
        answer = answer[4:]

    memory.save_context({'input': message}, {'output': answer})
    


    return jsonify({'response': answer})

if __name__ == '__main__':

    app.run(host = '0.0.0.0', port = 5000, debug=True)