import logging
import sys
from fastapi import FastAPI, Request
import torch
import os
os.environ['HF_HOME'] = '/llama3_models'
hf_access_token = os.getenv('HF_TOKEN')
model_id = os.getenv('LLAMA3_MODEL')
import transformers

# Logging
def get_logger(logger_name):
   logger = logging.getLogger(logger_name)
   logger.setLevel(logging.DEBUG)
   handler = logging.StreamHandler(sys.stdout)
   handler.setLevel(logging.DEBUG)
   handler.setFormatter(
      logging.Formatter(
      '%(name)s [%(asctime)s] [%(levelname)s] %(message)s'))
   logger.addHandler(handler)
   return logger
logger = get_logger('snowpark-container-service')

app = FastAPI()

logger.info('Loading Model ...')
pipeline = transformers.pipeline(
    "text-generation",
    model=model_id,
    model_kwargs={"torch_dtype": torch.bfloat16},
    device_map="auto",
    token=hf_access_token
)
logger.info('Finished Loading Model.')
   
@app.post("/complete", tags=["Endpoints"])
async def complete(request: Request):
   # input_prompt
   request_body = await request.json()
   request_body = request_body['data']
   return_data = []
   for index, input_prompt  in request_body:
      messages = [
          {"role": "system", "content": f"You are a helpful AI assistant."},
          {"role": "user", "content": f"{input_prompt}"},
      ]
      prompt = pipeline.tokenizer.apply_chat_template(
              messages, 
              tokenize=False, 
              add_generation_prompt=True
      )
      terminators = [
          pipeline.tokenizer.eos_token_id,
          pipeline.tokenizer.convert_tokens_to_ids("<|eot_id|>")
      ]
      outputs = pipeline(
          prompt,
          max_new_tokens=256,
          eos_token_id=terminators,
          do_sample=True,
          temperature=0.6,
          top_p=0.9
      )
      response = outputs[0]["generated_text"][len(prompt):]
      return_data.append([index, response])
   return {"data": return_data}
   
   
@app.post("/matillion_prompt", tags=["Endpoints"])
async def matillion_prompt(request: Request):
      
   request_body = await request.json()
   request_body = request_body['data']
   return_data = []
   for index, systemPrompt, userPrompt, inputValues, metadata  in request_body:
      messages = [
          {"role": "system", "content": f"{systemPrompt}"},
          {"role": "user", "content": f"{userPrompt} data object: {inputValues}"},
      ]
      prompt = pipeline.tokenizer.apply_chat_template(
              messages, 
              tokenize=False, 
              add_generation_prompt=True
      )
      terminators = [
          pipeline.tokenizer.eos_token_id,
          pipeline.tokenizer.convert_tokens_to_ids("<|eot_id|>")
      ]
      outputs = pipeline(
          prompt,
          max_new_tokens=1500,
          eos_token_id=terminators,
          do_sample=True,
          temperature=metadata['temperature'],
          top_p=1
      )
      response = outputs[0]["generated_text"][len(prompt):]
      return_data.append([index, response])
   return {"data": return_data}