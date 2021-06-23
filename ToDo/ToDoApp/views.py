from django.shortcuts import render, HttpResponseRedirect, reverse
import uuid
import datetime as dt
from datetime import datetime
from . import authentication
from . import datahandlers


def update_cookie_if_expired(is_expired, response, cookie_data):
    if is_expired:
        return authentication.update_cookie(response, cookie_data)
    else:
        return response


@authentication.login_required
def todos(request):
    name = authentication.get_cookie(request, ["name"])["name"]
    url = 'https://6w9ezcb22m.execute-api.ap-south-1.amazonaws.com/v1/{}/todos'

    is_expired, cookie_data, todo_list = datahandlers.handle_api_gateway(request, "get", url=url, get_item='Items')
    todo_list.sort(key=lambda x: (x["CompletionStatus"], datetime.strptime(x["CreationDateTime"], '%m/%d/%Y %H:%M:%S')))

    response = render(request, 'ToDoApp/todos.html', {"todo_list": todo_list, "user": name})
    return update_cookie_if_expired(is_expired, response, cookie_data)


@authentication.login_required
def detail(request, todo_id):
    name = authentication.get_cookie(request, ["name"])["name"]
    url = 'https://6w9ezcb22m.execute-api.ap-south-1.amazonaws.com/v1/{}/todos/{}'
    params = [todo_id]

    is_expired, cookie_data, todo = datahandlers.handle_api_gateway(request, "get", url=url, params=params,
                                                                    get_item='Item')

    response = render(request, 'ToDoApp/detail.html', {"todo": todo, "user": name})
    return update_cookie_if_expired(is_expired, response, cookie_data)


@authentication.login_required
def delete(request, todo_id):
    url = 'https://6w9ezcb22m.execute-api.ap-south-1.amazonaws.com/v1/{}/todos/{}'
    params = [todo_id]

    is_expired, cookie_data, data = datahandlers.handle_api_gateway(request, "delete", url=url, params=params)

    response = HttpResponseRedirect(reverse('ToDoApp:todos'))
    return update_cookie_if_expired(is_expired, response, cookie_data)


@authentication.login_required
def create(request):
    url = 'https://6w9ezcb22m.execute-api.ap-south-1.amazonaws.com/v1/{}/todos/{}'
    todo_id = str(uuid.uuid4())
    params = [todo_id]
    now = datetime.now()
    data = {
        "completionstatus": "N",
        "creationdatetime": now.strftime("%m/%d/%Y %H:%M:%S"),
        "tododescription": request.POST["description"]
    }

    is_expired, cookie_data, data = datahandlers.handle_api_gateway(request, "put", url=url, params=params, data=data)

    response = HttpResponseRedirect(reverse('ToDoApp:todos'))
    return update_cookie_if_expired(is_expired, response, cookie_data)


@authentication.login_required
def update(request, todo_id):
    url = 'https://6w9ezcb22m.execute-api.ap-south-1.amazonaws.com/v1/{}/todos/{}'
    params = [todo_id]
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

    is_expired, cookie_data, data = datahandlers.handle_api_gateway(request, "post", url=url, params=params, data=data)
    response = ''
    if request.POST.get("detailform", False):
        response = HttpResponseRedirect(reverse('ToDoApp:detail', args=(todo_id,)))
    elif request.POST.get("todosform", False):
        response = HttpResponseRedirect(reverse('ToDoApp:todos'))
    return update_cookie_if_expired(is_expired, response, cookie_data)


@authentication.is_user_already_logged_in
def signin(request):
    if request.POST:
        res = authentication.signin(request.POST)
        if res["error"] and res["message"] == 'User is not confirmed':
            return render(request, 'ToDoApp/verification_code.html', {'user': request.POST["email"]})
        elif res["error"]:
            return render(request, 'ToDoApp/signin.html', {'error_message': res["message"]})
        else:
            response = HttpResponseRedirect(reverse('ToDoApp:todos'))
            expiry_time = datetime.now() + dt.timedelta(seconds=res["data"]["expires_in"])
            res["data"]["expires_in"] = expiry_time.strftime("%m/%d/%Y %H:%M:%S")
            return authentication.set_cookie(response, res["data"])
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


def verifycode(request, user):
    if request.POST:
        data = {"code": request.POST.get("code"), "user": user}
        res = authentication.signup_confirmation(data)
        if res["error"]:
            return render(request, 'ToDoApp/verification_code.html', {'error_message': res["message"],
                                                                      'user': user
                                                                      })
        else:
            return HttpResponseRedirect(reverse('ToDoApp:signin'))
    return render(request, 'ToDoApp/verification_code.html', {'user': user})


def proceedsignin(request, user):
    return render(request, 'ToDoApp/proceedsignin.html', {'user': user})


def resendverifycode(request, user):
    resend_res = authentication.resend_verification_code({"user": user})
    if resend_res["error"] and resend_res["message"] == 'User is already confirmed':
        return HttpResponseRedirect(reverse('ToDoApp:proceedsignin', args=(user,)))
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
    response = HttpResponseRedirect(reverse('ToDoApp:signin'))
    return authentication.delete_cookie(response)


@authentication.login_required
def ask_for_logout(request):
    return render(request, 'ToDoApp/logout.html')
