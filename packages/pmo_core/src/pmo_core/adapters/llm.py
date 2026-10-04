"""Model factory: Foundry chat model and embeddings (API key locally, Managed Identity on Azure)."""

from __future__ import annotations

from typing import Any

from langchain_openai import AzureOpenAIEmbeddings

from pmo_core.settings import Settings

AZURE_COGNITIVE_SCOPE = "https://cognitiveservices.azure.com/.default"


def _auth_kwargs(settings: Settings) -> dict[str, Any]:
    """API key when configured; otherwise an Entra ID token provider."""
    if settings.foundry_api_key:
        return {"api_key": settings.foundry_api_key}
    from azure.identity import DefaultAzureCredential, get_bearer_token_provider

    return {
        "azure_ad_token_provider": get_bearer_token_provider(DefaultAzureCredential(), AZURE_COGNITIVE_SCOPE)
    }


def get_embeddings(settings: Settings) -> AzureOpenAIEmbeddings:
    """Embeddings for the configured deployment and dimensions."""
    return AzureOpenAIEmbeddings(
        azure_endpoint=settings.foundry_endpoint,
        deployment=settings.embedding_deployment,
        openai_api_version=settings.foundry_api_version,
        dimensions=settings.embedding_dimensions,
        chunk_size=64,
        max_retries=3,
        **_auth_kwargs(settings),
    )
