import os
# pyright: ignore [reportMissingImports]
import litellm
from pydantic import BaseModel
from typing import TypeVar, Type

litellm.drop_params = True
T = TypeVar('T', bound=BaseModel)

def call_llm(prompt: str, user_input: str, response_model: Type[T], model: str = "groq/llama-3.3-70b-versatile") -> T:
    import json
    from pydantic import ValidationError
    
    schema_str = json.dumps(response_model.model_json_schema())
    system_prompt = prompt + f"\n\nIMPORTANT: You must return a valid JSON object that strictly adheres to this JSON Schema:\n{schema_str}"
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ]
    
    max_reprompts = 2
    for attempt in range(max_reprompts + 1):
        try:
            response = litellm.completion(
                model=model,
                messages=messages,
                response_format={"type": "json_object"},
                num_retries=3,
                fallbacks=["gemini/gemini-2.5-flash"]
            )
            content = response.choices[0].message.content
            return response_model.model_validate_json(content)
        except ValidationError as e:
            if attempt == max_reprompts:
                raise e
            # Re-prompt the LLM with the validation error
            messages.append({"role": "assistant", "content": content})
            messages.append({"role": "user", "content": f"Your previous response failed validation. Please fix the following errors and try again:\n{e}"})

