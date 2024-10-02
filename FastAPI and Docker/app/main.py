# Importing dependecies
import os
import time
import asyncio
from fastapi import FastAPI
from pydantic import BaseModel

from app.pipeline import PromptEnhancer


# Setting up the API key for single project
# - create a .env file and add to it: OPENAI_API_KEY = the_personal_api_key
# - Or: go to pipeline.py and pass it there (not recommended)


app = FastAPI()

class InputPrompt(BaseModel):
    text: str
       
@app.post("/advanced_prompt_generation")
async def advancedPromptPipeline(payload: InputPrompt):
    
    input_prompt = payload.text
    
    model="gpt-4o-mini"
    
    if model == "gpt-4o":
        i_cost=5/10**6
        o_cost=15/10**6
    elif model == "gpt-4o-mini":
        i_cost=0.15/10**6
        o_cost=0.6/10**6
    
    enhancer = PromptEnhancer(model)
    
    start_time = time.time()
    advanced_prompt = await enhancer.enhance_prompt(input_prompt, perform_eval=False)
    elapsed_time = time.time() - start_time
    
    return {
        "model": model,
        "elapsed_time": elapsed_time,
        "prompt_tokens": enhancer.prompt_tokens,
        "completion_tokens": enhancer.completion_tokens,
        "approximate_cost": (enhancer.prompt_tokens*i_cost)+(enhancer.completion_tokens*o_cost),
        "inout_prompt": input_prompt,
        "advanced_prompt": advanced_prompt["advanced_prompt"],
    }
    


    