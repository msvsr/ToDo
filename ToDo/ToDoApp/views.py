from django.shortcuts import render, HttpResponseRedirect, reverse
import uuid
from datetime import datetime
from . import authentication
from . import datahandlers


@authentication.login_required
def todos(request, **kwargs):
    name = kwargs["name"]
    url = 'https://6w9ezcb22m.execute-api.ap-south-1.amazonaws.com/v1/{}/todos'

    todo_list = datahandlers.handle_api_gateway(request, "get", url=url, get_item='Items')
    todo_list.sort(key=lambda x: (x["CompletionStatus"], datetime.strptime(x["CreationDateTime"], '%m/%d/%Y %H:%M:%S')))

    return render(request, 'ToDoApp/todos.html', {"todo_list": todo_list, "user": name})


@authentication.login_required
def detail(request, todoid, **kwargs):
    name = kwargs["name"]
    url = 'https://6w9ezcb22m.execute-api.ap-south-1.amazonaws.com/v1/{}/todos/{}'
    params = [todoid]

    todo = datahandlers.handle_api_gateway(request, "get", url=url, params=params, get_item='Item')

    return render(request, 'ToDoApp/detail.html', {"todo": todo, "user": name})


@authentication.login_required
def delete(request, todoid, **kwargs):
    username, headers, name = kwargs["username"], kwargs["headers"], kwargs["name"]
    url = 'https://6w9ezcb22m.execute-api.ap-south-1.amazonaws.com/v1/{}/todos/{}'
    params = [todoid]

    datahandlers.handle_api_gateway(request, "delete", url=url, params=params)

    return HttpResponseRedirect(reverse('ToDoApp:todos'))


@authentication.login_required
def create(request, **kwargs):
    name = kwargs["name"]
    url = 'https://6w9ezcb22m.execute-api.ap-south-1.amazonaws.com/v1/{}/todos/{}'
    todoid = str(uuid.uuid4())
    params = [todoid]
    now = datetime.now()
    data = {
        "completionstatus": "N",
        "creationdatetime": now.strftime("%m/%d/%Y %H:%M:%S"),
        "tododescription": request.POST["description"]
    }

    datahandlers.handle_api_gateway(request, "put", url=url, params=params, data=data)

    return HttpResponseRedirect(reverse('ToDoApp:todos'))


@authentication.login_required
def update(request, todoid, **kwargs):
    name = kwargs["name"]
    url = 'https://6w9ezcb22m.execute-api.ap-south-1.amazonaws.com/v1/{}/todos/{}'
    params = [todoid]
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

    datahandlers.handle_api_gateway(request, "post", url=url, params=params, data=data)

    if request.POST.get("detailform", False):
        return HttpResponseRedirect(reverse('ToDoApp:detail', args=(todoid,)))
    elif request.POST.get("todosform", False):
        return HttpResponseRedirect(reverse('ToDoApp:todos'))


@authentication.is_user_already_logged_in
def signin(request):
    if request.POST:
        res = authentication.signin(request.POST)
        if res["error"] and res["message"] == 'User is not confirmed':
            return render(request, 'ToDoApp/verification_code.html', {'user': request.POST["email"]})
        elif res["error"]:
            return render(request, 'ToDoApp/signin.html', {'error_message': res["message"]})
        else:
            cookie_data = {"usersession": str(uuid.uuid4())}
            cookie_data.update(**res["data"])
            response = HttpResponseRedirect(reverse('ToDoApp:todos'))
            return authentication.setcookie(response, cookie_data)
    return render(request, 'ToDoApp/signin.html')


@authentication.is_user_already_logged_in
def signup(request):
    if request.POST:
        res = authentication.signup(request.POST)
        if res["error"]:
            return render(request, 'ToDoApp/signup.html', {'error_message': res["message"]})
        else:
            return render(request, 'ToDoApp/verification_code.html', {'user': request.POST["email"]})
    else:
        return render(request, 'ToDoApp/signup.html')


@authentication.login_required
def verifycode(request, user):
    data = {"code": request.POST.get("code"), "user": user}
    res = authentication.signup_confirmation(data)
    if res["error"]:
        return render(request, 'ToDoApp/verification_code.html', {'error_message': res["message"],
                                                                  'user': user
                                                                  })
    else:
        return HttpResponseRedirect(reverse('ToDoApp:todos'))


@authentication.login_required
def resendverifycode(request, user):
    resend_res = authentication.resend_verification_code({"user": user})
    return HttpResponseRedirect(reverse('ToDoApp:code', args=(user,)))


@authentication.is_user_already_logged_in
def forgot_password(request):
    if request.POST:
        user = request.POST["email"]
        fg_pass = authentication.forgot_password({"username": user})

        if fg_pass["success"]:
            return render(request, "ToDoApp/confirm_forgot_password.html", {"message": fg_pass["message"]})
        return render(request, "ToDoApp/forgot_password.html", {"error_message": fg_pass["message"]})
    return render(request, "ToDoApp/forgot_password.html")


@authentication.is_user_already_logged_in
def confirm_forgot_password(request):
    if request.POST:
        user = request.POST["email"]
        code = request.POST["code"]
        password = request.POST["password"]
        fg_pass = authentication.confirm_forgot_password({"username": user, "code": code, "password": password})

        if fg_pass["success"]:
            return render(request, "ToDoApp/signin.html")
        return render(request, "ToDoApp/confirm_forgot_password.html", {"error_message": fg_pass["message"]})
    return render(request, "ToDoApp/confirm_forgot_password.html")


@authentication.login_required
def log_out(request):
    authentication.deletecookie(request)
    return render(request, 'ToDoApp/signin.html')


@authentication.login_required
def ask_for_logout(request):
    return render(request, 'ToDoApp/logout.html')
