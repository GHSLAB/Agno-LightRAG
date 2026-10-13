"""
App Settings
============

Shared runtime objects for the platform.
"""

from os import getenv

from agno.models.openai.like import OpenAILike


def default_model() -> OpenAILike:
    """Fresh model instance per agent — avoids shared-state footguns."""
    return OpenAILike(
        id="MiniMax-M3",
        api_key=getenv("MINIMAX_API_KEY"),
        base_url="https://api.minimaxi.com/v1",
        provider="MiniMax",
        extra_body={"reasoning_split": True},
        supports_native_structured_outputs=False,
    )
