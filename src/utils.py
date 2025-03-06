import json

import aiofiles


async def load_json(file_path: str):
    async with aiofiles.open(file_path, "r") as f:
        try:
            data = await f.read()
            return json.loads(data)
        except json.JSONDecodeError:
            return None


async def save_json(file_path: str, data):
    async with aiofiles.open(file_path, "w") as f:
        await f.write(json.dumps(data, indent=4))


async def append_to_json(file_path: str, data):
    # Load existing data or create new list
    try:
        async with aiofiles.open(file_path, "r") as f:
            content = await f.read()
            existing_data = json.loads(content) if content else []
    except (FileNotFoundError, json.JSONDecodeError):
        existing_data = []

    # Ensure existing_data is a list
    if not isinstance(existing_data, list):
        existing_data = []

    # Append new data
    existing_data.append(data)

    # Save updated list
    async with aiofiles.open(file_path, "w") as f:
        await f.write(json.dumps(existing_data, indent=4))
