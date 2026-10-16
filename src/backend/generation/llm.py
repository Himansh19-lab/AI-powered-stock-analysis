
from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel
from typing import Optional
import os
from dotenv import load_dotenv

from backend.utils.logger import Logger

load_dotenv()

class LLMFactory:
    logger = Logger(name="LLMFactory",log_file='llm_generation.py',level='DEBUG')

    PROVIDER_KEY_MAP = {
        "openai": "OPENAI_API_KEY",
        "google_genai": "GOOGLE_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
    }

    @classmethod
    def _validate_env_keys(cls,model_provider: str):
        """
        Validate the API key exists in os.environ
        Args:
            model_provider (str): Provider of the model to be initialized.
        Returns:
            None
        """
        env_var_name = cls.PROVIDER_KEY_MAP.get(model_provider.lower())
        if env_var_name:
            api_key = os.environ.get(env_var_name)
            if not api_key:
                cls.logger.error(f"Missing {env_var_name} in environment / .env file")
                raise ValueError(
                    f"API key for '{model_provider}' not found. "
                    f"Please set '{env_var_name}' in your .env file or environment."
                )

    @classmethod
    def get_llm(cls,model_name: str ="gpt-4o-mini",model_provider: str ="openai",
                temperature: float =0.1, max_tokens: Optional[int]= 2048) -> BaseChatModel:
        """

        Initialising LLM  and a LangChain BaseChatModel
        Args:
            model_name (str): Name of the model to be initialized.
            model_provider (str): Provider of the model to be initialized.
            temperature (float): Temperature of the model to be initialized.
            max_tokens (Optional[int]): Maximum number of tokens to be generated.
        Returns:
            BaseChatModel: Configured chat model instance.
        """
      
        cls._validate_env_keys(model_provider)
        cls.logger.info(f"Initializing LLM: model='{model_name}', provider='{model_provider}', temp={temperature}")
        try:
            llm = init_chat_model(
                model_name=model_name,
                provider=model_provider,
                temperature=temperature,
                max_tokens=max_tokens,
        )
            cls.logger.info("LLM initialized successfully")
            return llm
        except Exception as e:
            cls.logger.error(f"Error initializing LLM: {e}")
            raise e


if __name__ == "__main__":
    llm = LLMFactory.get_llm()
    print(llm)
    
   