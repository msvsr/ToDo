from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
import requests
from . import authenticationexceptions
from . import authentication
from datetime import datetime


def convert_to_python_format(data):
    deserializer = TypeDeserializer()
    return {k: deserializer.deserialize(v) for k, v in data}


def convert_to_dynamodb_format(data):
    serializer = TypeSerializer()
    return serializer.serialize(data)['M']


def check_response_for_unauthorized(response):
    message = response.json().get("message")
    if message is not None:
        if message == "The incoming token has expired":
            raise authenticationexceptions.TokenExpired
        elif response.json().get("message") == "Unauthorized":
            raise authenticationexceptions.Unauthorized


def handle_api_gateway(request, method, url, params=None, data=None, get_item=''):
    # Setting to corresponding type if the parameters are None
    if data is None:
        data = {}
    if params is None:
        params = []

    # Calling appropriate method
    try:
        for i in range(6):
            is_expired, cookie_data = authentication.get_headers(request)
            username, headers = cookie_data["email"], {"Authorization": cookie_data["id_token"]}
            url = url.format(username, *params)
            return_data = ''
            if method == "get":
                response = requests.get(url=url, headers=headers)
                check_response_for_unauthorized(response)
                if get_item == 'Item':
                    return_data = convert_to_python_format(response.json().get('Item').items())
                elif get_item == 'Items':
                    return_data = [convert_to_python_format(item.items()) for item in response.json().get('Items')]
            elif method == "post":
                response = requests.post(url=url, json=data, headers=headers)
                check_response_for_unauthorized(response)
            elif method == "put":
                response = requests.put(url=url, json=data, headers=headers)
                check_response_for_unauthorized(response)
            elif method == "delete":
                response = requests.delete(url=url, headers=headers)
                check_response_for_unauthorized(response)

            return is_expired, cookie_data, return_data
        else:
            raise Exception("Error")
    except authenticationexceptions.TokenExpired:
        pass
    except authenticationexceptions.Unauthorized:
        pass
