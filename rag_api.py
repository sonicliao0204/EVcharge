from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
import os

# 初始化 FastAPI
app = FastAPI(title="充電樁技術知識庫 RAG API")

# 請替換為您實際的 API Key，或設定在環境變數中
os.environ["OPENAI_API_KEY"] = "your-api-key-here"

# 初始化嵌入模型與 LLM
embeddings = OpenAIEmbeddings()
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2) # 溫度設低，確保維修建議的精準與穩定性

# 初始化本地端 Chroma 向量資料庫
vector_store = Chroma(
    collection_name="ev_tech_kb",
    embedding_function=embeddings,
    persist_directory="./chroma_db" # 向量資料會存在這個資料夾
)

# 定義 API 接收的資料格式
class LogRequest(BaseModel):
    log_content: str

class KBItem(BaseModel):
    category: str
    issue: str
    solution: str

@app.post("/ingest_kb")
async def ingest_knowledge_base(item: KBItem):
    """
    接收技術文件並轉化為向量存入資料庫
    可以將原有的 tech_kb.json 寫腳本批次打進這個 Endpoint
    """
    doc_text = f"分類: {item.category}\n問題: {item.issue}\n解決方案: {item.solution}"
    vector_store.add_texts(texts=[doc_text])
    return {"message": "✅ 技術文件已成功向量化並存入知識庫"}

@app.post("/analyze_log")
async def analyze_ocpp_log(request: LogRequest):
    """
    接收前端傳來的 OCPP Log，進行相似度檢索並交由 LLM 分析
    """
    if not request.log_content:
        raise HTTPException(status_code=400, detail="請提供 Log 內容")

    # 1. 將資料庫轉為檢索器 (Retriever)，設定抓取最相關的 3 筆技術文件
    retriever = vector_store.as_retriever(search_kwargs={"k": 3})

    # 2. 設計專屬的維修診斷 Prompt 模板
    template = """
    你是一位專業的電動車充電樁 (EVSE) 維護工程師與 OCPP 協定專家。
    請根據以下「已知技術知識庫」的內容，來分析工程師提供的「系統 Log」，並給出具體的排障建議。
    如果知識庫的內容不足以完全解決問題，請基於你的 OCPP 與 ISO 15118 專業知識進行補充，但必須標示為補充建議。

    【已知技術知識庫】:
    {context}

    【系統 Log】:
    {log}

    請以 HTML 格式輸出回答（直接使用 <div>, <strong>, <ul>, <li> 等標籤，不要包含 ```html 的 markdown 標記），
    結構需包含：
    1. 🚨 診斷結果 (一句話總結問題點)
    2. 🔍 特徵分析 (解釋 Log 中發生了什麼事)
    3. 🛠️ 行動建議 (列點說明現場工程師或後台管理員該如何處置)
    """
    
    prompt = ChatPromptTemplate.from_template(template)

    # 3. 建立 LangChain 的 RAG 處理管線 (Chain)
    rag_chain = (
        {"context": retriever, "log": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    try:
        # 執行分析
        diagnosis_result = rag_chain.invoke(request.log_content)
        return {"diagnosis_html": diagnosis_result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # 啟動本機伺服器
    uvicorn.run(app, host="0.0.0.0", port=8000)
