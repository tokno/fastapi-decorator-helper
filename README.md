# Usage
```python
from fastapi_decorator_helper import DecoratorHelper, ExecutePathOperator

def require_api_key(api_key):
    helper = DecoratorHelper()

    @helper.wraps
    def wrapper(request: Request, next: ExecutePathOperator):
        if request.headers.get('Authorization') != api_key:
            return Response(status_code=403, content=json.dumps({
                'detail': 'invalid api key'
            }))

        return next()

    return wrapper
```

```python
from fastapi import FastAPI, Request, Response

app = FastAPI()

@app.get('/hello')
@require_api_key('xxx')
def hello(name: str):
    return {
        'message': f'hello {name}',
    }
```
