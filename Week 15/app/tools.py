import json
import httpx

async def get_weather(city: str) -> str:
    async with httpx.AsyncClient(timeout=10) as http:
        geo = (await http.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1},
        )).json()
        if not geo.get("results"):
            return f"Could not find location: {city}"
        lat, lon = geo["results"][0]["latitude"], geo["results"][0]["longitude"]
        weather = (await http.get(
            "https://api.open-meteo.com/v1/forecast",
            params={"latitude": lat, "longitude": lon, "current_weather": True},
        )).json()
    temp = weather["current_weather"]["temperature"]
    return f"Current temperature in {city} is {temp}°C."

def calculator(expression: str) -> str:
    try:
        return str(eval(expression, {"__builtins__": {}}))
    except Exception as e:
        return f"Error: {e}"

TOOLS = [
    {"type": "function", "function": {
        "name": "get_weather", "description": "Get current weather for a city",
        "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]},
    }},
    {"type": "function", "function": {
        "name": "calculator", "description": "Evaluate a basic arithmetic expression",
        "parameters": {"type": "object", "properties": {"expression": {"type": "string"}}, "required": ["expression"]},
    }},
]

async def execute_tool_calls(messages: list, tool_calls) -> list:
    for tc in tool_calls:
        args = json.loads(tc.function.arguments)
        if tc.function.name == "get_weather":
            result = await get_weather(**args)
        elif tc.function.name == "calculator":
            result = calculator(**args)
        else:
            result = f"Unknown tool: {tc.function.name}"
        messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
    return messages