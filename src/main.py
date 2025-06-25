from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from src.database import init_database
from src.workflow import create_workflow
from src.logger import setup_logger, request_id_context
import uuid
from langchain_core.messages import HumanMessage, AIMessage
import uvicorn

logger = setup_logger()
app = FastAPI()

db = init_database()
agent = create_workflow(db)

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request_id_context.set(request_id)
    logger.debug(f"Starting request | path={request.url.path} method={request.method}")
    response = await call_next(request)
    logger.debug(f"Completed request | status_code={response.status_code}")
    return response

class QuestionInput(BaseModel):
    question: str

@app.post("/chat")
async def chat(request: Request, question_input: QuestionInput):
    logger.info(f"Received request | question={question_input.question}")
    try:
        question = question_input.question.strip()
        if not question:
            logger.warning("Invalid input | error=empty_question")
            raise HTTPException(status_code=400, detail="Question cannot be empty")

        final_query = None
        for step in agent.stream(
            {"messages": [HumanMessage(content=question)]},
            stream_mode="values",
        ):
            last_message = step["messages"][-1]
            logger.debug(f"Workflow step | message=\n{last_message.content}")
            if isinstance(last_message, AIMessage) and last_message.content.strip():
                if last_message.content.startswith("Error:"):
                    logger.error(f"Workflow error | error={last_message.content}")
                    raise HTTPException(status_code=500, detail=last_message.content)
                final_query = last_message.content

        if final_query:
            logger.info(f"Returning response | query=\n{final_query}")
            return {"query": final_query}
        else:
            logger.warning("No query generated")
            raise HTTPException(status_code=404, detail="No SQL query generated")

    except HTTPException as e:
        logger.error(f"HTTP error | status={e.status_code} detail={e.detail}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error | error={str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

if __name__ == "__main__":
    logger.info("Starting FastAPI application")
    uvicorn.run(app, host="0.0.0.0", port=8000)