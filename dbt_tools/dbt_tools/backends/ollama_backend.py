from typing import Iterable
from .base import LLMBackend
import ollama
import os


class OllamaBackend(LLMBackend):
    """
    LLM backend for generating documentation using a local or remote Ollama instance.

    This backend reads configuration primarily from environment variables:

    Environment Variables
    ---------------------
    - ``OLLAMA_MODEL`` : str  
        Name of the Ollama model to use (e.g., ``llama3.1:8b-instruct-q8_0``).  
        Defaults to ``llama3.1:8b-instruct-q8_0`` if unset.

    - ``OLLAMA_HOST`` : str  
        Base URL of the Ollama server (e.g., ``http://localhost:11434``).  
        Defaults to ``http://localhost:11434`` if unset.

    Parameters
    ----------
    model : str, optional
        Explicit model name. Overrides ``OLLAMA_MODEL`` if provided.
    temperature : float, optional
        Sampling temperature (default: 0.2).
    host : str, optional
        Ollama server URL. Overrides ``OLLAMA_HOST`` if provided.

    Notes
    -----
    - Requires the Ollama Python package and a running Ollama daemon.
    - Responses are trimmed of whitespace and yielded one per prompt.
    """

    def __init__(
        self
    ):
        # Read defaults from environment if not explicitly provided
        self.model = os.getenv("OLLAMA_MODEL", "llama3.1:8b-instruct-q8_0")
        self.temperature = os.getenv("TEMPERATURE", 0.2)
        self.host = os.getenv("OLLAMA_HOST", "http://localhost:11434")

        # Create client bound to the configured host
        self.client = ollama.Client(host=self.host)

    def generate(self, prompts: Iterable[str]) -> Iterable[str]:
        """
        Generate LLM responses for a sequence of prompts.

        Parameters
        ----------
        prompts : Iterable[str]
            Iterable of prompt strings to send to the Ollama API.

        Yields
        ------
        str
            One text response per prompt, stripped of leading/trailing whitespace.
        """
        for p in prompts:
            rsp = self.client.generate(
                model=self.model,
                prompt=p,
                options={"temperature": float(self.temperature)},
            )
            yield rsp["response"].strip()