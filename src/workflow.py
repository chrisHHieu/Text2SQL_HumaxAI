from langchain.chat_models import init_chat_model
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from typing import Literal
from src.config import Config
from src.logger import setup_logger

logger = setup_logger()

def create_workflow(db: SQLDatabase):
    logger.info("Initializing LLM and SQL toolkit")
    try:
        llm = init_chat_model(
            model="gpt-4.1-mini",
            api_key=Config.OPENAI_API_KEY,
            model_provider="openai"
        )
        toolkit = SQLDatabaseToolkit(db=db, llm=llm)
        tools = toolkit.get_tools()
        logger.info("LLM and toolkit initialized")
    except Exception as e:
        logger.error(f"Failed to initialize LLM or toolkit | error={str(e)}", exc_info=True)
        raise

    logger.info("Defining tool nodes")
    get_schema_tool = next(tool for tool in tools if tool.name == "sql_db_schema")
    get_schema_node = ToolNode([get_schema_tool], name="get_schema")
    logger.info("Tool nodes defined")

    def list_tables(state: MessagesState):
        logger.info("Entering node | node=list_tables")
        try:
            tool_call = {
                "name": "sql_db_list_tables",
                "args": {},
                "id": "abc123",
                "type": "tool_call",
            }
            tool_call_message = AIMessage(content="", tool_calls=[tool_call])
            list_tables_tool = next(tool for tool in tools if tool.name == "sql_db_list_tables")
            logger.debug("Invoking tool | tool=sql_db_list_tables")
            tool_message = list_tables_tool.invoke(tool_call)
            response = AIMessage(f"Available tables: {tool_message.content}")
            logger.info(f"Node completed | node=list_tables tables={tool_message.content}")
            return {"messages": [tool_call_message, tool_message, response]}
        except Exception as e:
            logger.error(f"Node failed | node=list_tables error={str(e)}", exc_info=True)
            return {"messages": [AIMessage(content=f"Error listing tables: {str(e)}")]}

    def call_get_schema(state: MessagesState):
        logger.info("Entering node | node=call_get_schema")
        try:
            llm_with_tools = llm.bind_tools([get_schema_tool], tool_choice="any")
            logger.debug("Invoking LLM for schema retrieval")
            response = llm_with_tools.invoke(state["messages"])
            logger.info("Node completed | node=call_get_schema")
            return {"messages": [response]}
        except Exception as e:
            logger.error(f"Node failed | node=call_get_schema error={str(e)}", exc_info=True)
            return {"messages": [AIMessage(content=f"Error retrieving schema: {str(e)}")]}

    generate_query_system_prompt = """
    You are an agent designed to interact with a SQL database.
    Given an input question, create a syntactically correct {dialect} query to run,
    then look at the results of the query and return the answer. Unless the user
    specifies a specific number of examples they wish to obtain

    You can order the results by a relevant column to return the most interesting
    examples in the database. Never query for all the columns from a specific table,
    only ask for the relevant columns given the question.

    DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database.
    """.format(dialect=db.dialect)

    def generate_query(state: MessagesState):
        logger.info("Entering node | node=generate_query")
        try:
            system_message = SystemMessage(content=generate_query_system_prompt)
            question = state['messages'][-1].content
            logger.debug(f"Processing question | question={question}")
            response = llm.invoke([system_message] + state["messages"])
            query = response.content.strip()
            logger.info(f"Node completed | node=generate_query query=\n{query}")
            return {"messages": [AIMessage(content=query)]}
        except Exception as e:
            logger.error(f"Node failed | node=generate_query error={str(e)}", exc_info=True)
            return {"messages": [AIMessage(content=f"Error generating query: {str(e)}")]}

    check_query_system_prompt = """
    You are a SQL expert for a {dialect} database.
    Review the provided SQL query for common errors, including:
    - NOT IN with NULL values
    - UNION instead of UNION ALL
    - BETWEEN for exclusive ranges
    - Data type mismatches in predicates
    - Incorrect identifier quoting
    - Wrong number of function arguments
    - Improper casting
    - Incorrect join columns

    If errors are found, rewrite the query to fix them. If no errors, return the original query.
    Return only the SQL query as plain text, without explanations or markdown.
    """.format(dialect=db.dialect)

    def check_query(state: MessagesState):
        logger.info("Entering node | node=check_query")
        try:
            system_message = SystemMessage(content=check_query_system_prompt)
            last_message = state["messages"][-1]
            if not isinstance(last_message, AIMessage) or not last_message.content.strip():
                logger.error("No valid query found | node=check_query")
                return {"messages": [AIMessage(content="Error: No query generated")]}
            user_message = HumanMessage(content=last_message.content)
            logger.debug(f"Checking query | query=\n{last_message.content}")
            response = llm.invoke([system_message, user_message])
            checked_query = response.content.strip()
            logger.info(f"Node completed | node=check_query checked_query=\n{checked_query}")
            return {"messages": [AIMessage(content=checked_query)]}
        except Exception as e:
            logger.error(f"Node failed | node=check_query error={str(e)}", exc_info=True)
            return {"messages": [AIMessage(content=f"Error checking query: {str(e)}")]}

    def should_continue(state: MessagesState) -> Literal[END, "check_query"]: # type: ignore
        last_message = state["messages"][-1]
        result = "check_query" if isinstance(last_message, AIMessage) and last_message.content.strip() and not last_message.content.startswith("Error:") else END
        logger.debug(f"Routing decision | node=generate_query next={result}")
        return result

    logger.info("Building LangGraph workflow")
    builder = StateGraph(MessagesState)
    builder.add_node(list_tables)
    builder.add_node(call_get_schema)
    builder.add_node(get_schema_node, "get_schema")
    builder.add_node(generate_query)
    builder.add_node(check_query)

    builder.add_edge(START, "list_tables")
    builder.add_edge("list_tables", "call_get_schema")
    builder.add_edge("call_get_schema", "get_schema")
    builder.add_edge("get_schema", "generate_query")
    builder.add_conditional_edges("generate_query", should_continue)
    builder.add_edge("check_query", END)

    logger.info("Compiling agent")
    agent = builder.compile()
    logger.info("Agent compiled")
    return agent