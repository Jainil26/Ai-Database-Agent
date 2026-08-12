import os
import json
import pymysql
from openai import AsyncOpenAI  
from dotenv import load_dotenv
from datetime import datetime
import chainlit as cl

load_dotenv()

client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1", 
    api_key=os.getenv("OPENROUTER_API_KEY")
)

class DatabaseJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        import decimal
        import datetime

        if isinstance(obj, decimal.Decimal):
            return float(obj)

        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()

        return super(DatabaseJsonEncoder, self).default(obj)

SQL_RULEBOOK = """
You are a text-to-SQL translator. 
Database Schema:
- categories (category_id, name)
- products (product_id, category_id, product_name, status)
- product_variants (variant_id, product_id, sku, price)
- customers (customer_id, first_name, last_name, email)
- orders (order_id, customer_id, order_status, total_amount)

Rules:
- Reply ONLY with the raw MySQL query string.
- Do not explain it or use markdown code blocks.
"""

def ask_database(question):
    print(f"   ↳ [DB Sub-Agent]: Translating question -> '{question}'")
    try:
        import requests
        headers = {
            "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "openrouter/free", 
            "messages": [
                {"role": "system", "content": SQL_RULEBOOK},
                {"role": "user", "content": question}
            ],
            "temperature": 0.0
        }
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        ai_sql_response = response.json()
        generated_sql = ai_sql_response['choices'][0]['message']['content'].strip()

        connection = pymysql.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            cursorclass=pymysql.cursors.DictCursor,
        )

        try:
            with connection.cursor() as cursor:
                cursor.execute(generated_sql)
                raw_database_results = cursor.fetchall()
        finally:
            connection.close()

        return json.dumps(raw_database_results, cls=DatabaseJsonEncoder)
    
    except Exception as err:
        return f"Error executing database tool: {str(err)}"

def get_time():
    return str(datetime.now())

def say_hello():
    return "Hello Jainil!"

def get_agent_name():
    return "I am Agent Jarvis!!"

def create_file(filename, content):
    with open(filename, "w") as target_files:
        target_files.write(content)
    print(f"File {filename} Created successfully!!")
    return f"Success: Created '{filename}' with the requested contents."

def read_file(filename):
    try:
        with open(filename, "r", encoding="utf-8") as target_file:
            content = target_file.read()
        print(f"File {filename} Read successfully!!")
        return f"Content of '{filename}':\n{content}"
    except Exception as e:
        return f"Error reading file: {str(e)}"

tools = {
    "get_time": get_time,
    "say_hello": say_hello,
    "get_agent_name": get_agent_name,
    "create_file": create_file,
    "read_file": read_file,
    "ask_database": ask_database,
}

sdk_tools = [
    {
        "type": "function",
        "function": {
            "name": "ask_database",
            "description": "Queries the internal e-commerce database to check orders, product variants, stock statuses, prices, categories, and customer records.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The specific natural language question about products, customers, or orders to check against the schema tables.",
                    }
                },
                "required": ["question"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_time",
            "description": "Get the current date and time.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "say_hello",
            "description": "Greets the user warmly.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_agent_name",
            "description": "Retrieves the name of the AI agent.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_file",
            "description": "Creates a single file with a specified filename and writes specific content inside it. Call this multiple times to generate multiple files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "The name of the file to create, including its extension (e.g., 'notes.txt').",
                    },
                    "content": {
                        "type": "string",
                        "description": "The exact text data to write inside the file.",
                    },
                },
                "required": ["filename", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Reads and returns the text contents of a local file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "The exact name of the file to read (e.g., 'notes.txt').",
                    }
                },
                "required": ["filename"],
            },
        },
    },
]

MAX_MEMORY = 20


@cl.on_chat_start
async def start():
    cl.user_session.set("history", [])


@cl.on_message
async def main(message: cl.Message):
    history = cl.user_session.get("history")
    
    # Emergency fallback initialization 
    if not history:
        history = [
            {
                "role": "system",
                "content": """You are Jarvis, a helpful AI assistant. 
CRITICAL OPERATING DIRECTIVES:
1. NEVER reply conversationally with phrases like "Okay", "I can do that", or "Sure" if the user has requested local actions. Jump directly into generating tool calls.
2. If a task requires information you don't have (like the current date/time), your very first action step MUST be to call the `get_time` tool.
3. This is a multi-step execution loop. When you get data back from a tool, immediately use it to execute the next tool in the chain.
4. Only output a final text summary when absolutely all file creations, calculations, or reads are completely finished."""
            }
        ]

    history.append({"role": "user", "content": message.content})

    status_msg = cl.Message(content="🤖 Jarvis is planning the workflow...")
    await status_msg.send()

    while True:
        response = await client.chat.completions.create(
            model="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",  
            messages=history,
            tools=sdk_tools,
            temperature=0.0,
        )

        assistant_reply = response.choices[0].message
        history.append(assistant_reply)

        if not assistant_reply.tool_calls:
            if assistant_reply.content:
                final_answer = assistant_reply.content
            elif hasattr(assistant_reply, "reasoning") and assistant_reply.reasoning:
                final_answer = assistant_reply.reasoning
            else:
                final_answer = "Mission Completed Successfully."

            if "<tool_call" in final_answer or "<function" in final_answer:
                final_answer = "I have successfully processed your complex workflow."

            await cl.Message(content=final_answer).send()
            await status_msg.remove()
            break

        for tool_call in assistant_reply.tool_calls:
            function_name = tool_call.name if hasattr(tool_call, 'name') else tool_call.function.name
            
            
            status_msg.content = f"⚙️ Running Active Tool: `{function_name}`..."
            await status_msg.update()

            if function_name in tools:
                tool_fun = tools[function_name]
                args = tool_call.function.arguments
                
                if args:
                    parsed_args = json.loads(args)
                    result = tool_fun(**parsed_args)
                else:
                    result = tool_fun()

                if function_name == "ask_database":
                    try:
                        parsed_data = json.loads(result)
                        if isinstance(parsed_data, list) and len(parsed_data) > 0:
                            result = f"Database query result rows: {str(parsed_data)}"
                    except Exception:
                        pass

                history.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": str(result),
                    }
                )

    while len(history) > MAX_MEMORY:
        history.pop(1)

    cl.user_session.set("history", history)