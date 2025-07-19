import asyncio
import functools
from typing import Any, Callable, TypeVar, Union
from concurrent.futures import ThreadPoolExecutor
import threading

T = TypeVar('T')

class ServiceBase:
    """Base class para servicios que necesitan trabajar en modo sync/async"""
    
    def __init__(self):
        self._executor = ThreadPoolExecutor(max_workers=4)
    
    def _is_async_context(self) -> bool:
        """Detectar si estamos en un contexto async"""
        try:
            loop = asyncio.get_running_loop()
            return True
        except RuntimeError:
            return False
    
    async def _run_in_executor(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Ejecutar función síncrona en executor"""
        loop = asyncio.get_running_loop()
        partial_func = functools.partial(func, *args, **kwargs)
        return await loop.run_in_executor(self._executor, partial_func)
    
    def _make_sync_async_compatible(self, func: Callable[..., T]) -> Callable[..., Union[T, Any]]:
        """Crear una versión de función que funcione en ambos contextos"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if self._is_async_context():
                # Estamos en contexto async, usar executor
                return self._run_in_executor(func, *args, **kwargs)
            else:
                # Contexto sync, ejecutar directamente
                return func(*args, **kwargs)
        
        return wrapper
