
from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel
from typing import Optional


from backend.utils.logger import Logger


class LLMFactory:
    logger = Logger(name="LLMFactory",log_file='llm_generation.py',level='DEBUG')

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
    
   