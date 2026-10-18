

from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel
from typing import Optional
import os
from langchain_aws import ChatBedrockConverse
from dotenv import load_dotenv

from backend.utils.logger import Logger

load_dotenv()

from backend.utils.config import config

class LLMFactory:
    logger = Logger(name="LLMFactory", log_file='llm_generation.log', level='DEBUG')

    PROVIDER_KEY_MAP = {
        "openai": "OPENAI_API_KEY",
        "google_genai": "GOOGLE_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "bedrock": "AWS_ACCESS_KEY_ID",
    }

    @classmethod
    def _validate_env_keys(cls, model_provider: str):
        provider = model_provider.lower()
        if provider in ("bedrock", "aws"):
            if not (os.environ.get("AWS_ACCESS_KEY_ID") or os.environ.get("AWS_PROFILE")):
                cls.logger.warning("AWS_ACCESS_KEY_ID not found in env; falling back to ~/.aws/credentials or IAM role.")
            return

        env_var_name = cls.PROVIDER_KEY_MAP.get(provider)
        if env_var_name:
            api_key = os.environ.get(env_var_name)
            if not api_key:
                cls.logger.error(f"Missing {env_var_name} in environment / .env file")
                raise ValueError(
                    f"API key for '{model_provider}' not found. "
                    f"Please set '{env_var_name}' in your .env file or environment."
                )
        else:
            raise ValueError(
                f"Model provider '{model_provider}' not supported."
            )

    @classmethod
    def get_llm(
        cls,
        model_name: Optional[str] = None,
        model_provider: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> BaseChatModel:
        model_name = model_name or config.llm.model_name
        model_provider = model_provider or config.llm.provider
        temperature = temperature if temperature is not None else config.llm.temperature
        max_tokens = max_tokens or config.llm.max_tokens
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
            if model_provider.lower() in ("bedrock", "aws"):                
                region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
                model = os.environ.get("BEDROCK_MODEL_ID") or model_name
                kwargs = {
                    "model": model,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "region_name": region,
                }
                if os.environ.get("AWS_ACCESS_KEY_ID") and os.environ.get("AWS_SECRET_ACCESS_KEY"):
                    kwargs["aws_access_key_id"] = os.environ.get("AWS_ACCESS_KEY_ID")
                    kwargs["aws_secret_access_key"] = os.environ.get("AWS_SECRET_ACCESS_KEY")
                
                llm = ChatBedrockConverse(**kwargs)
                cls.logger.info(f"Bedrock Converse LLM initialized successfully with model '{model}' in region '{region}'")
                return llm
            
            else:
                llm = init_chat_model(
                    model=model_name,
                    model_provider=model_provider,
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

    
   