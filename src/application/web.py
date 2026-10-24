"""Controller discovery with convention-based feature routing."""

from importlib import import_module
from inspect import isclass
from pathlib import Path

from fastapi import APIRouter

from src.infrastructure.di.inject import DependencyError, inject
from src.infrastructure.utils.config_reader import ConfigReader


@inject
class WebService:
    def __init__(self, config_reader: ConfigReader):
        self._config = config_reader

    def api(self) -> APIRouter:
        router = APIRouter(prefix=self._config.get_api_prefix())
        root = Path(__file__).resolve().parent
        for feature in sorted(p for p in root.iterdir() if p.is_dir() and not p.name.startswith("_")):
            if not (feature / f"{feature.name}_controller.py").is_file():
                # Directories without a controller are not HTTP features.
                continue
            try:
                module = import_module(f"src.application.{feature.name}.{feature.name}_controller")
                controller_name = "".join(part.title() for part in feature.name.split("_")) + "Controller"
                controller = getattr(module, controller_name)
                if not isclass(controller) or not controller.__dict__.get("__di_inject__", False):
                    raise DependencyError("CONTROLLER_INVALID")
                feature_router = controller().api()
                if not isinstance(feature_router, APIRouter):
                    raise DependencyError("CONTROLLER_INVALID")
                router.include_router(feature_router, prefix="/" + feature.name)
            except Exception:
                raise DependencyError("CONTROLLER_DISCOVERY_FAILED") from None
        return router
