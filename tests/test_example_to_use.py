from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient
from fastapi_decorator_helper import DecoratorHelper, ExecutePathOperator
import json

app = FastAPI()


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


@app.get('/hello')
@require_api_key('xxx')
def hello(name: str):
    return {
        'message': f'hello {name}',
    }


client = TestClient(app)


def test_return_403_response_if_api_key_absent():
    response = client.get('/hello?name=world')
    print(response.json())

    assert response.status_code == 403
    assert response.json() == {
        'detail': 'invalid api key'
    }

def test_return_200_response_if_valid_api_key_present():
    response = client.get('/hello?name=world', headers={'Authorization':'xxx'})

    assert response.status_code == 200
    assert response.json() == {
        'message': 'hello world'
    }
