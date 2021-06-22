from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
import requests
from . import authenticationexceptions
from . import authentication


def convert_to_python_format(data):
    deserializer = TypeDeserializer()
    return {k: deserializer.deserialize(v) for k, v in data}


def convert_to_dynamodb_format(data):
    serializer = TypeSerializer()
    return serializer.serialize(data)['M']


def check_response_for_unauthorized(response):
    message = response.json().get("message")
    print(message)
    if message == "The incoming token has expired":
        raise authenticationexceptions.TokenExpired
    if response.json().get("message") == "Unauthorized":
        raise authenticationexceptions.Unauthorized


def handle_api_gateway(request, method, url, params=None, data=None, get_item=''):
    # Setting to corresponding type if the parameters are None
    if data is None:
        data = {}
    if params is None:
        params = []

    username, headers, name = authentication.get_user(request)
    url = url.format(username, *params)

    # Calling appropriate method
    try:
        if method == "get":
            response = requests.get(url=url, headers=headers)
            check_response_for_unauthorized(response)
            if get_item == 'Item':
                return convert_to_python_format(response.json().get('Item').items())
            elif get_item == 'Items':
                return [convert_to_python_format(item.items()) for item in response.json().get('Items')]
        elif method == "post":
            response = requests.post(url=url, json=data, headers=headers)
            check_response_for_unauthorized(response)
        elif method == "put":
            response = requests.put(url=url, json=data, headers=headers)
            check_response_for_unauthorized(response)
        elif method == "delete":
            response = requests.delete(url=url, headers=headers)
            check_response_for_unauthorized(response)
    except authenticationexceptions.TokenExpired:
        authentication.get_refreshed_headers(request)
        handle_api_gateway(request, method, url, params, data, get_item)
        pass
