from django.shortcuts import render, HttpResponseRedirect, reverse
import requests
from boto3.dynamodb.types import TypeDeserializer
import uuid
from datetime import datetime
from . import authentication

user_details = {}


def convert_to_python_format(data):
    deserializer = TypeDeserializer()
    return {k: deserializer.deserialize(v) for k, v in data}


def todos(request):
    username = True
    if not username:
        return render(request, 'ToDoApp/signup.html')
    response = requests.get('https://6w9ezcb22m.execute-api.ap-south-1.amazonaws.com/v1/msvsr/todos')
    todo_list = [convert_to_python_format(item.items()) for item in response.json().get('Items')]
    todo_list.sort(key=lambda x: (x["CompletionStatus"], datetime.strptime(x["CreationDateTime"], '%m/%d/%Y %H:%M:%S')))
    return render(request, 'ToDoApp/todos.html', {"todo_list": todo_list})


def detail(request, todoid):
    response = requests.get('https://6w9ezcb22m.execute-api.ap-south-1.amazonaws.com/v1/msvsr/todos/{}'.format(todoid))
    todo = convert_to_python_format(response.json().get('Item').items())
    return render(request, 'ToDoApp/detail.html', {"todo": todo})


def delete(request, todoid):
    response = requests.delete(
        'https://6w9ezcb22m.execute-api.ap-south-1.amazonaws.com/v1/msvsr/todos/{}'.format(todoid))
    return HttpResponseRedirect(reverse('ToDoApp:todos'))


def create(request):
    now = datetime.now()
    todoid = str(uuid.uuid4())
    data = {
        "completionstatus": "N",
        "creationdatetime": now.strftime("%m/%d/%Y %H:%M:%S"),
        "tododescription": request.POST["description"]
    }
    response = requests.put(
        'https://6w9ezcb22m.execute-api.ap-south-1.amazonaws.com/v1/msvsr/todos/{}'.format(todoid),
        json=data)
    return HttpResponseRedirect(reverse('ToDoApp:todos'))


def update(request, todoid):
    now = datetime.now()
    if request.POST.get("completionstatus", False):
        data = {
            "completionstatus": "Y",
            "completiondatetime": now.strftime("%m/%d/%Y %H:%M:%S")
        }
    else:
        data = {
            "completionstatus": "N"
        }

    response = requests.post(
        'https://6w9ezcb22m.execute-api.ap-south-1.amazonaws.com/v1/msvsr/todos/{}'.format(todoid),
        json=data)
    if request.POST.get("detailform", False):
        return HttpResponseRedirect(reverse('ToDoApp:detail', args=(todoid,)))
    elif request.POST.get("todosform", False):
        return HttpResponseRedirect(reverse('ToDoApp:todos'))


def signup(request):
    res = authentication.signup(request.POST)
    if res["error"]:
        return render(request, 'ToDoApp/signup.html', {'error_message': res["message"]})
    else:
        return render(request, 'ToDoApp/verification_code.html', {'user': request.POST["email"]})


def verifycode(request, user):
    data = {"code": request.POST.get("code"), "user": user}
    res = authentication.signup_confirmation(data)
    if res["error"]:
        return render(request, 'ToDoApp/verification_code.html', {'error_message': res["message"],
                                                                  'user': user
                                                                  })
    else:
        return HttpResponseRedirect(reverse('ToDoApp:todos'))


def resendverifycode(request, user):
    resend_res = authentication.resend_verification_code({"user": user})
    return HttpResponseRedirect(reverse('ToDoApp:code', args=(user,)))
