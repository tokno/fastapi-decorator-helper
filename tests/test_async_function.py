from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient
from fastapi_decorator_helper import DecoratorHelper, ExecutePathOperator
import json

app = FastAPI()


def sync_decorator():
    helper = DecoratorHelper()

    @helper.wraps
    def wrapper(next: ExecutePathOperator):
        return next()

    return wrapper


@app.get('/sync-sync')
@sync_decorator()
def sync_path_operator_with_sync_decorator():
    return {
        'message': 'sync-sync',
    }


@app.get('/async-sync')
@sync_decorator()
async def async_path_operator_with_sync_decorator():
    return {
        'message': 'async-sync',
    }


client = TestClient(app)


def test_sync_path_operator_with_sync_decorator():
    response = client.get('/sync-sync')

    assert response.status_code == 200
    assert response.json() == {
        'message': 'sync-sync'
    }


def test_async_path_operator_with_sync_decorator():
    response = client.get('/async-sync')

    assert response.status_code == 200
    assert response.json() == {
        'message': 'async-sync'
    }
