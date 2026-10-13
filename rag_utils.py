
import os
import streamlit as st
from dotenv import load_dotenv
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import SQLChatMessageHistory, ChatMessageHistory
from system_template import SYSTEM_TEMPLATE
from database_utils import DB_PATH
from constants import ENV_DEFAULTS, RAG_MAX_DOCS, RAG_TEMPERATURE, RAG_MAX_TOKENS, RAG_TIMEOUT_SECONDS
from error_handlers import safe_execute

def validate_environment_variables():
    """Validate required environment variables with defaults"""
    required_vars = ["PINECONE_API_KEY", "OPENAI_API_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    return {
        "pinecone_api_key": os.getenv("PINECONE_API_KEY"),
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "index_name": os.getenv("PINECONE_INDEX_NAME", ENV_DEFAULTS["PINECONE_INDEX_NAME"]),
        "openai_model": os.getenv("OPENAI_MODEL", ENV_DEFAULTS["OPENAI_MODEL"]),
        "embedding_model": os.getenv("EMBEDDING_MODEL", ENV_DEFAULTS["EMBEDDING_MODEL"])
    }

@st.cache_resource(show_spinner=False)
def load_rag_chain():
    """Loads the RAG components with comprehensive error handling and caching."""
    try:
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        load_dotenv(env_path)
        
        env_vars = validate_environment_variables()
        
        embeddings = safe_execute(
            lambda: HuggingFaceEmbeddings(
                model_name=env_vars["embedding_model"],
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            ),
            "Embeddings initialization"
        )
        if not embeddings:
            raise ValueError("Failed to initialize embeddings model")
        
        llm = safe_execute(
            lambda: ChatOpenAI(
                model_name=env_vars["openai_model"],
                temperature=RAG_TEMPERATURE,
                streaming=True,
                max_tokens=RAG_MAX_TOKENS,
                timeout=RAG_TIMEOUT_SECONDS,
                max_retries=3,
                model_kwargs={
                    "frequency_penalty": 0,
                    "presence_penalty": 0
                }
            ),
            "LLM initialization"
        )
        if not llm:
            raise ValueError("Failed to initialize LLM")
        
        vectorstore = safe_execute(
            lambda: PineconeVectorStore.from_existing_index(
                index_name=env_vars["index_name"], 
                embedding=embeddings
            ),
            "Vector store initialization"
        )
        if not vectorstore:
            raise ValueError("Failed to connect to vector store")
            
        retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": RAG_MAX_DOCS}
        )
        
        rephrase_prompt = ChatPromptTemplate.from_messages([
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            ("user", "Given the above conversation, generate a concise, standalone search query to retrieve relevant legal documents and information.")
        ])
        
        history_aware_retriever = create_history_aware_retriever(
            llm, retriever, rephrase_prompt
        )
        
        final_prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_TEMPLATE + """

CRITICAL FORMATTING INSTRUCTIONS:
- You MUST maintain all formatting, markdown syntax, and exact structure in your response
- Follow the specified format templates precisely from the system template
- Preserve all table formatting, bullet points, and visual elements
- Use the retrieved context below to inform your response

**Context from retrieved documents:**
{context}"""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
        ])
        
        question_answer_chain = create_stuff_documents_chain(llm, final_prompt)
        rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
        
      
        return rag_chain
        
    except Exception as e:
        raise ValueError(f"RAG system initialization failed: {str(e)}")

def get_session_history(session_id: str):
    """Return SQLChatMessageHistory instance for a session id with fallback."""
    try:
        if not session_id:
            raise ValueError("Session ID cannot be empty")
        
        connection_string = f"sqlite:///{DB_PATH}"
        
        history = SQLChatMessageHistory(
            session_id=session_id, 
            connection_string=connection_string,
            table_name="message_store"
        )
        
        return history
        
    except Exception as e:
        return ChatMessageHistory()

def create_conversational_chain(rag_chain):
    """Create conversational RAG chain with message history."""
    try:
        if not rag_chain:
            raise ValueError("RAG chain cannot be None")
        
        conversational_chain = RunnableWithMessageHistory(
            rag_chain,
            get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer",
        )
        
        return conversational_chain
        
    except Exception as e:
        raise ValueError(f"Conversational chain creation failed: {str(e)}")

def clear_session_history(session_id: str):
    """Clear chat history for a specific session."""
    if not session_id:
        return False
    
    return safe_execute(
        lambda: get_session_history(session_id).clear(),
        f"Clear session history for {session_id}",
        show_error=False
    ) is not None

def get_rag_system_info():
    """Get information about the RAG system configuration"""
    try:
        env_vars = validate_environment_variables()
        
        return {
            "index_name": env_vars["index_name"],
            "embedding_model": env_vars["embedding_model"],
            "llm_model": env_vars["openai_model"],
            "database_path": DB_PATH,
            "max_retrieval_docs": RAG_MAX_DOCS,
            "temperature": RAG_TEMPERATURE,
            "max_tokens": RAG_MAX_TOKENS
        }
    except Exception as e:
        return {"error": str(e)}

def create_fallback_chain():
    """Create a simple fallback chain when full RAG fails"""
    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.prompts import ChatPromptTemplate
        
        llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=RAG_TEMPERATURE,
            max_tokens=1000
        )
        
        fallback_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a legal assistant. Provide helpful responses about Indian law, but inform the user that the full document search system is currently unavailable."),
            ("user", "{input}")
        ])
        
        return fallback_prompt | llm
        
    except Exception as e:
        return None

def handle_rag_error(error, fallback=True):
    """Handle RAG errors gracefully with optional fallback"""
   
    
    if fallback:
        fallback_chain = create_fallback_chain()
        if fallback_chain:
            return fallback_chain, "Using simplified response system (document search unavailable)"
    
    return None, f"Legal assistant temporarily unavailable: {str(error)}"