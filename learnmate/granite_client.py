"""
learnmate/granite_client.py
───────────────────────────
Thin wrapper around IBM watsonx.ai (ibm-watsonx-ai SDK) for the
IBM Granite model family.  Uses the /ml/v1/text/chat (chat completions)
API which is the current recommended endpoint.
"""

import os
from typing import Optional

from dotenv import load_dotenv
from ibm_watsonx_ai import APIClient, Credentials
from ibm_watsonx_ai.foundation_models import ModelInference

load_dotenv()


class GraniteClient:
    """
    Wraps IBM Granite on watsonx.ai.

    Environment variables required:
        IBM_API_KEY          – IBM Cloud IAM API key
        WATSONX_PROJECT_ID   – watsonx.ai project ID
        WATSONX_URL          – service endpoint URL
        GRANITE_MODEL_ID     – model ID (e.g. ibm/granite-3-8b-instruct)
        MAX_NEW_TOKENS       – maximum tokens to generate   (default 1024)
        TEMPERATURE          – sampling temperature         (default 0.7)
        TOP_P                – nucleus sampling p           (default 0.9)
    """

    def __init__(self) -> None:
        api_key = os.getenv("IBM_API_KEY", "")
        url = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
        self.project_id = os.getenv("WATSONX_PROJECT_ID", "")
        self.model_id = os.getenv("GRANITE_MODEL_ID", "ibm/granite-3-8b-instruct")

        if not api_key or api_key == "your_ibm_api_key_here":
            raise EnvironmentError(
                "IBM_API_KEY is not set. "
                "Please edit your .env file with a valid IBM Cloud IAM API key.\n"
                "Get one at: https://cloud.ibm.com/iam/apikeys"
            )
        if not self.project_id or self.project_id == "your_watsonx_project_id_here":
            raise EnvironmentError(
                "WATSONX_PROJECT_ID is not set. "
                "Please edit your .env file with a valid watsonx.ai project ID.\n"
                "Find it in: https://dataplatform.cloud.ibm.com → your project → Manage"
            )

        self._max_tokens = int(os.getenv("MAX_NEW_TOKENS", "1024"))
        self._temperature = float(os.getenv("TEMPERATURE", "0.7"))
        self._top_p = float(os.getenv("TOP_P", "0.9"))

        credentials = Credentials(url=url, api_key=api_key)
        self._client = APIClient(credentials=credentials, project_id=self.project_id)

        try:
            self._model = ModelInference(
                model_id=self.model_id,
                api_client=self._client,
                project_id=self.project_id,
            )
        except Exception as exc:
            raise EnvironmentError(
                f"Failed to load model '{self.model_id}': {exc}\n"
                "Check GRANITE_MODEL_ID in your .env file.\n"
                "Run: python -c \"from ibm_watsonx_ai import APIClient, Credentials; "
                "c=APIClient(Credentials(url=__import__('os').getenv('WATSONX_URL'), "
                "api_key=__import__('os').getenv('IBM_API_KEY'))); "
                "print(c.foundation_models.TextModels)\" to list available models."
            ) from exc

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, prompt: str, max_new_tokens: Optional[int] = None) -> str:
        """
        Send a plain-text prompt to IBM Granite via the chat completions API.
        Wraps the prompt as a single user message.
        """
        messages = [{"role": "user", "content": prompt}]
        return self._chat(messages, max_new_tokens=max_new_tokens)

    def generate_with_history(self, messages: list[dict], system_prompt: str = "") -> str:
        """
        Send a chat-history list to IBM Granite via the chat completions API.

        Args:
            messages:      List of {"role": "user"|"assistant"|"system", "content": "…"}
            system_prompt: Prepended as a system message if provided.
        """
        full_messages: list[dict] = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt.strip()})
        full_messages.extend(messages)
        return self._chat(full_messages)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _chat(self, messages: list[dict], max_new_tokens: Optional[int] = None) -> str:
        """Call the /ml/v1/text/chat endpoint and return the assistant reply."""
        params = {
            "max_tokens": max_new_tokens or self._max_tokens,
            "temperature": self._temperature,
            "top_p": self._top_p,
        }
        response = self._model.chat(messages=messages, params=params)
        # SDK returns a dict; extract content from choices[0].message.content
        try:
            return response["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError):
            # Fallback: str-cast the whole response
            return str(response).strip()
