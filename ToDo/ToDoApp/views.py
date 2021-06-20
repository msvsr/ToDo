from django.shortcuts import render, HttpResponseRedirect, reverse
import requests
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
import uuid
from datetime import datetime
from . import authentication
import boto3


def convert_to_python_format(data):
    deserializer = TypeDeserializer()
    return {k: deserializer.deserialize(v) for k, v in data}


def convert_to_dynamodb_format(data):
    serializer = TypeSerializer()
    return serializer.serialize(data)['M']


def setcookie(request, key_value=None):
    request.set_cookie("usersession", key_value["usersession"])
    dynamodb = boto3.client("dynamodb")
    data = {
        "TableName": "usersession",
        "Item": convert_to_dynamodb_format(key_value)
    }
    dynamodb.put_item(**data)
    return request


def getcookie(request):
    try:
        usersession = request.COOKIES["usersession"]
        dynamodb = boto3.client("dynamodb")

        data = {
            "TableName": "usersession",
            "Key": convert_to_dynamodb_format({"usersession": usersession})
        }
        response = dynamodb.get_item(**data)
        return convert_to_python_format(response.get('Item').items())
    except (KeyError, AttributeError):
        return None


def deletecookie(request):
    try:
        usersession = request.COOKIES["usersession"]
        dynamodb = boto3.client("dynamodb")

        data = {
            "TableName": "usersession",
            "Key": convert_to_dynamodb_format({"usersession": usersession})
        }
        dynamodb.delete_item(**data)
    except Exception as e:
        print(e)


def todos(request):
    cookiedetails = getcookie(request)
    if not cookiedetails:
        return render(request, 'ToDoApp/signin.html')
    headers = {"Authorization": cookiedetails["id_token"]}
    username = cookiedetails["email"]
    response = requests.get('https://6w9ezcb22m.execute-api.ap-south-1.amazonaws.com/v1/{}/todos'.format(username), headers=headers)
    message=response.json().get("message")
    if message == "Unauthorized":
        pass
    todo_list = [convert_to_python_format(item.items()) for item in response.json().get('Items')]
    todo_list.sort(key=lambda x: (x["CompletionStatus"], datetime.strptime(x["CreationDateTime"], '%m/%d/%Y %H:%M:%S')))
    return render(request, 'ToDoApp/todos.html', {"todo_list": todo_list, "user": getcookie(request)["name"]})


def detail(request, todoid):
    cookiedetails = getcookie(request)
    if not cookiedetails:
        return render(request, 'ToDoApp/signin.html')
    headers = {"Authorization": cookiedetails["id_token"]}
    username = cookiedetails["email"]
    response = requests.get('https://6w9ezcb22m.execute-api.ap-south-1.amazonaws.com/v1/{}/todos/{}'.format(username, todoid),
                            headers=headers)
    todo = convert_to_python_format(response.json().get('Item').items())
    return render(request, 'ToDoApp/detail.html', {"todo": todo})


def delete(request, todoid):
    cookiedetails = getcookie(request)
    if not cookiedetails:
        return render(request, 'ToDoApp/signin.html')
    headers = {"Authorization": cookiedetails["id_token"]}
    username = cookiedetails["email"]
    response = requests.delete(
        'https://6w9ezcb22m.execute-api.ap-south-1.amazonaws.com/v1/{}/todos/{}'.format(username, todoid),
        headers=headers)
    return HttpResponseRedirect(reverse('ToDoApp:todos'))


def create(request):
    cookiedetails = getcookie(request)
    if not cookiedetails:
        return render(request, 'ToDoApp/signin.html')
    headers = {"Authorization": cookiedetails["id_token"]}
    username = cookiedetails["email"]
    now = datetime.now()
    todoid = str(uuid.uuid4())
    data = {
        "completionstatus": "N",
        "creationdatetime": now.strftime("%m/%d/%Y %H:%M:%S"),
        "tododescription": request.POST["description"]
    }
    response = requests.put(
        'https://6w9ezcb22m.execute-api.ap-south-1.amazonaws.com/v1/{}/todos/{}'.format(username, todoid),
        json=data, headers=headers)
    return HttpResponseRedirect(reverse('ToDoApp:todos'))


def update(request, todoid):
    cookiedetails = getcookie(request)
    if not cookiedetails:
        return render(request, 'ToDoApp/signin.html')
    headers = {"Authorization": cookiedetails["id_token"]}
    username = cookiedetails["email"]
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
        'https://6w9ezcb22m.execute-api.ap-south-1.amazonaws.com/v1/{}/todos/{}'.format(username, todoid),
        json=data,headers=headers)
    if request.POST.get("detailform", False):
        return HttpResponseRedirect(reverse('ToDoApp:detail', args=(todoid,)))
    elif request.POST.get("todosform", False):
        return HttpResponseRedirect(reverse('ToDoApp:todos'))


def signin(request):
    if request.POST:
        res = authentication.signin(request.POST)
        if res["error"] and res["message"] == 'User is not confirmed':
            return render(request, 'ToDoApp/verification_code.html', {'user': request.POST["email"]})
        elif res["error"]:
            return render(request, 'ToDoApp/signin.html', {'error_message': res["message"]})
        else:
            response = HttpResponseRedirect(reverse('ToDoApp:todos'))
            cookie_data = {"usersession": str(uuid.uuid4())}
            cookie_data.update(**res["data"])
            response = HttpResponseRedirect(reverse('ToDoApp:todos'))
            return setcookie(response, cookie_data)
    return render(request, 'ToDoApp/signin.html')


def signup(request):
    if request.POST:
        res = authentication.signup(request.POST)
        if res["error"]:
            return render(request, 'ToDoApp/signup.html', {'error_message': res["message"]})
        else:
            return render(request, 'ToDoApp/verification_code.html', {'user': request.POST["email"]})
    else:
        return render(request, 'ToDoApp/signup.html')


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


def log_out(request):
    deletecookie(request)
    return render(request, 'ToDoApp/signin.html')
