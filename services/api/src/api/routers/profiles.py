"""Configuration profiles for the UI."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from api.deps import get_container
from api.schemas import ProfileOut
from pmo_core.container import Container

router = APIRouter(tags=["profiles"])


@router.get("/profiles", response_model=list[ProfileOut])
def list_profiles(container: Annotated[Container, Depends(get_container)]) -> list[ProfileOut]:
    """List profiles with their resolved toggles."""
    return [
        ProfileOut.model_validate({"name": name, "toggles": profile.toggles()})
        for name, profile in container.profiles.items()
    ]
