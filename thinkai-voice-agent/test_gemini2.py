import os
import asyncio
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv('.env')

async def run():
    client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))
    
    tool_book = types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name="book_appointment",
                description="Books an appointment",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "title": types.Schema(type=types.Type.STRING)
                    }
                )
            )
        ]
    )

    contents = [{"role": "user", "parts": [{"text": "Book an appointment for consultation"}]}]

    response = await client.aio.models.generate_content(
        model='gemini-2.5-flash',
        contents=contents,
        config=types.GenerateContentConfig(
            tools=[tool_book]
        )
    )
    
    # gemini returns a Content object that we can append directly
    contents.append(response.candidates[0].content)

    if response.function_calls:
        parts = []
        for fc in response.function_calls:
            parts.append({"functionResponse": {"name": fc.name, "response": {"result": "Success"}}})
            
        contents.append({"role": "user", "parts": parts})

        response2 = await client.aio.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents,
            config=types.GenerateContentConfig(
                tools=[tool_book]
            )
        )
        print("Final response:", response2.text)

asyncio.run(run())
