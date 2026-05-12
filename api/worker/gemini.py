import base64

from google import genai
from google.genai import types
from google.genai.types import HttpOptions


MODEL_NAME = "gemini-2.5-flash"
http_options = HttpOptions()
http_options.client_args = {"proxy": "http://SoyiZY9uuq:y3rmeKOQ5N@37.32.30.24:34036"}


async def generate(api_key, prompt, images):
    client = genai.Client(api_key=api_key, http_options=http_options)

    contents = []

    for image in images:
        image_bytes = base64.b64decode(image["data"])

        contents.append(
            types.Part.from_bytes(
                data=image_bytes,
                mime_type=image["mime_type"]
            )
        )

    contents.append(prompt)

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=contents
    )

    return response.text