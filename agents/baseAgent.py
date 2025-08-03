import json
import os
import openai
from utilities import constants as ct
from dotenv import load_dotenv
from typing import Dict, Any, Optional, Type
from abc import ABC

load_dotenv()
from pydantic import BaseModel
from openai import OpenAI
from dataclasses import dataclass


@dataclass
class UserProfile:
    age: int
    height: float  # in cm
    weight: float  # in kg
    sex: str  # 'M' or 'F'
    ambitions: str  # what is the user training for?
    current_job: str  # what does the user do as a job?


class LLMBase(ABC):
    """
    Abstract base calss for calling an LLM via the OpenAI API
    """

    def __init__(self, model: str = "grok-3-mini", temperature: float = 0.7, max_tokens: int = 1000):
        """
        Initialise the LLM base class with OpenAI API configuration
        :param model:
        :param temperature: controls randomness --> 0.0 to 1.0
        :param max_token: Maximum tokens in the response
        """
        self.api_key = os.getenv(ct.OPENAI_API_KEY)
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environmnet variables. Please set in the .env file")
        self.client = OpenAI(api_key=self.api_key, base_url="https://api.x.ai/v1")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.state = {"data": {}, "metadata": {}}

    def _call_openai(self, prompt: str, system_message: str = "You are a helpful assistant. ") -> Dict[str, Any]:
        """
        Internal method to call the OpenAI Api.
        :param prompt:
        :param system_message:
        :return: Dict[str, Any]: Raw response from OpenAI API.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            return response.to_dict()
        except openai.OpenAIError as e:
            raise RuntimeError(f"Open AI Api call failed:: {str(e)}")

    def parse_response(self, response: Dict[str, Any], pydantic_model: Optional[Type[BaseModel]] = None) -> Any:
        """
        Parse the OpenAI API response.

        :param response:
        :param pydantic_model:
        :return:  Any Parsed response, either as Pydantic model or raw content.
        """
        try:
            content = response['choices'][0]['message']['content']
            if pydantic_model:
                parsed_content = json.loads(content)
                return pydantic_model(
                    **parsed_content)  # the ** operator unpacks the dictioanry into keyword arguments!
            return content
        except Exception as e:
            raise ValueError(F"Failed to parse the OpenAI Api response: {str(e)}")

    def call_llm(self, input_data: Dict[str, Any], system_message: str = "You are a helpful assistant.",
                 pydantic_model: Optional[Type[BaseModel]] = None,
                 agent_name: str = "generic_agent") -> Any:
        """
        Main method to call the LLM via the OpenAI API
        :param input_data:
        :param system_message:
        :param pydantic_model:
        :param agent_name:
        :return:
        """

        raw_response = self._call_openai(prompt=input_data, system_message=system_message)
        result = self.parse_response(raw_response, pydantic_model)
        #  Update state for tracking
        self.state['data'][agent_name] = {
            "input": input_data,
            "response": result.__dict__ if isinstance(result, BaseModel) else result
        }
        return result
