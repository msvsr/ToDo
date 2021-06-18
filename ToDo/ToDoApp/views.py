from django.shortcuts import render, HttpResponseRedirect, reverse
import requests
from boto3.dynamodb.types import TypeDeserializer


def convert_to_python_format(data):
    deserializer = TypeDeserializer()
    return {k: deserializer.deserialize(v) for k, v in data}


def todos(request):
    response = requests.get('https://6w9ezcb22m.execute-api.ap-south-1.amazonaws.com/v1/msvsr/todos')
    todo_list = [convert_to_python_format(item.items()) for item in response.json().get('Items')]
    return render(request, 'ToDoApp/todos.html', {"todo_list": todo_list})


def detail(request, todoid):
    response = requests.get('https://6w9ezcb22m.execute-api.ap-south-1.amazonaws.com/v1/msvsr/todos/{}'.format(todoid))
    todo = convert_to_python_format(response.json().get('Item').items())
    return render(request, 'ToDoApp/detail.html', {"todo": todo})


def delete(request, todoid):
    response = requests.delete('https://6w9ezcb22m.execute-api.ap-south-1.amazonaws.com/v1/msvsr/todos/{}'.format(todoid))
    return HttpResponseRedirect(reverse('ToDoApp:todos'))

