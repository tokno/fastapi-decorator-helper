import asyncio
from collections import OrderedDict
from inspect import Parameter, signature, Signature
from typing import Any, Callable, Dict, List, Tuple

ExecutePathOperation = Callable[[], Any]


def _is_parameter_conflicts(param: Parameter, params: OrderedDict[str, Parameter]):
    if param.kind in [Parameter.VAR_KEYWORD, Parameter.VAR_POSITIONAL]:
        return False

    if param.name not in params:
        return False

    param2 = params[param.name]

    if param.default == param2.default:
        return False

    if param.annotation == param2.annotation:
        return False

    return True


def arg_position_priority(param: Parameter):
    if param.kind == Parameter.VAR_KEYWORD:
        return 5

    if param.kind == Parameter.VAR_POSITIONAL:
        return 4

    if param.kind == Parameter.KEYWORD_ONLY:
        return 3

    if param.kind == Parameter.POSITIONAL_ONLY:
        return 2

    if param.default != Parameter.empty:
        return 1

    return 0


class ArgumentProcessor:
    def __init__(self, path_operation: Callable, decorator: Callable):
        self.path_operation = path_operation
        self.decorator = decorator

        self._initialize()

    def _initialize(self):
        path_operation_signature = signature(self.path_operation)
        decorator_signature = signature(self.decorator)

        # raise if parameter conflicts
        for param in path_operation_signature.parameters.values():
            if _is_parameter_conflicts(param, decorator_signature.parameters):
                raise f'duplicated parameter name {param.name}'

        self._path_operation_signature = path_operation_signature
        self._decorator_signature = decorator_signature

    @property
    def merged_signature(self) -> Signature:
        params = []
        
        for param in self._path_operation_signature.parameters.values():
            params.append(param)

        for param in self._decorator_signature.parameters.values():
            if param.kind in [Parameter.VAR_POSITIONAL, Parameter.VAR_KEYWORD]:
                continue

            if param.annotation == ExecutePathOperation:
                continue

            params.append(param)

        params.sort(key=arg_position_priority)

        return Signature(parameters=params)

    def execute_decorator(self, *args, **kwargs):
        _args, _kwargs = self._get_decorator_arguments(*args, **kwargs)
        return self.decorator(*_args, **_kwargs)

    def _get_path_operation_arguments(self, *args, **kwargs) -> Tuple[List, Dict]:
        _args = []
        _kwargs = {}

        for param in self._path_operation_signature.parameters.values():
            _kwargs[param.name] = kwargs[param.name]

        return _args, _kwargs

    def _get_decorator_arguments(self, *args, **kwargs) -> Tuple[List, Dict]:
        _args = []
        _kwargs = {}

        def execute_path_operation():
            _args, _kwargs = self._get_path_operation_arguments(*args, **kwargs)

            if asyncio.iscoroutinefunction(self.path_operation):
                return asyncio.run(self.path_operation(*_args, **_kwargs))
            else:
                return self.path_operation(*_args, **_kwargs)

        for param in self._decorator_signature.parameters.values():
            if param.annotation == ExecutePathOperation:
                _kwargs[param.name] = execute_path_operation
                continue

            _kwargs[param.name] = kwargs[param.name]

        return _args, _kwargs


class DecoratorHelper:
    def wraps(self, decorator):
        def wrapper(func):
            self.argument_processor = ArgumentProcessor(func, decorator)

            def decorator_wrapper(*args, **kwargs):
                return self.argument_processor.execute_decorator(*args, **kwargs)

            decorator_wrapper.__doc__ = func.__doc__
            decorator_wrapper.__signature__ = self.argument_processor.merged_signature

            return decorator_wrapper

        return wrapper
