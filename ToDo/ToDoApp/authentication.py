import boto3
import hmac
import hashlib
import base64
from functools import wraps
from django.shortcuts import HttpResponseRedirect, reverse
import datetime

USER_POOL_ID = 'ap-south-1_8PyMwWLc2'
CLIENT_ID = '694kesb6nn07juejiuur45l0gv'
CLIENT_SECRET = '1f9ep3mu9tqctee884707vgrm4bpck4jkgq5uajhq8fmrvfqmcs2'


def set_cookie(request, cookie_data=None):
    if cookie_data is None:
        cookie_data = {}
    for cookie_name in cookie_data:
        request.set_cookie(cookie_name, cookie_data[cookie_name])
    request.set_cookie("is_cookie_on", "1")
    return request


def get_cookie(request, cookie_names=None):
    if cookie_names is None:
        cookie_names = []
    if not cookie_names:
        return request.COOKIES
    cookie_data = {cookie_name: request.COOKIES[cookie_name] for cookie_name in cookie_names}
    return cookie_data


def update_cookie(request, cookie_data=None):
    if cookie_data is None:
        cookie_data = {}
    return set_cookie(request, cookie_data)


def delete_cookie(request):
    request.set_cookie("is_cookie_on", "0")
    return request


def get_new_token_if_expired(request):
    expires_in = get_cookie(request, ['expires_in'])["expires_in"]
    if datetime.datetime.now() > datetime.datetime.strptime(expires_in, "%m/%d/%Y %H:%M:%S"):
        sub_refresh_token = get_cookie(request, ["sub", "refresh_token"])
        refreshed_cookie = get_refreshed_tokens(sub_refresh_token["sub"], sub_refresh_token["refresh_token"])
        expiry_time = refreshed_cookie["expires_in"]
        refreshed_cookie["expires_in"] = expiry_time.strftime("%m/%d/%Y %H:%M:%S")
        return refreshed_cookie


def get_headers(request):
    refreshed_cookies = get_new_token_if_expired(request)
    if refreshed_cookies:
        return True, refreshed_cookies
    cookies = get_cookie(request, ["email", 'id_token'])
    return False, cookies


def login_required(view_function):
    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        def sign_in():
            return HttpResponseRedirect(reverse('ToDoApp:signin'))
        cookiedetails = get_cookie(args[0])
        if not cookiedetails:
            return sign_in()
        elif not int(cookiedetails.get("is_cookie_on", 0)):
            return sign_in()
        else:
            return view_function(*args, **kwargs)

    return decorated_function


def is_user_already_logged_in(view_function):
    @wraps(view_function)
    def decorated_function(*args, **kwargs):

        cookiedetails = get_cookie(args[0])

        def log_out():
            return HttpResponseRedirect(reverse('ToDoApp:askforlogout'))

        if cookiedetails:
            if int(cookiedetails.get('is_cookie_on', 0)):
                return log_out()
            else:
                return view_function(*args, **kwargs)
        return view_function(*args, **kwargs)

    return decorated_function


def get_secret_hash(username):
    msg = username + CLIENT_ID
    dig = hmac.new(str(CLIENT_SECRET).encode('utf-8'),
                   msg=str(msg).encode('utf-8'), digestmod=hashlib.sha256).digest()
    d2 = base64.b64encode(dig).decode()
    return d2


def signup(event, context=None):
    email, password, name = event["email"], event['password'], event["name"]
    client = boto3.client('cognito-idp')
    try:
        resp = client.sign_up(
            ClientId=CLIENT_ID,
            SecretHash=get_secret_hash(email),
            Username=email,
            Password=password,
            UserAttributes=[
                {
                    'Name': "name",
                    'Value': name
                },
                {
                    'Name': "email",
                    'Value': email
                }
            ],
            ValidationData=[
                {
                    'Name': "email",
                    'Value': email
                }
            ])

    except client.exceptions.UsernameExistsException as e:
        return {"error": True,
                "success": False,
                "message": "This username already exists",
                "data": None}
    except client.exceptions.InvalidPasswordException as e:

        return {"error": True,
                "success": False,
                "message": "Password should have Caps,\
                          Special chars, Numbers",
                "data": None}
    except client.exceptions.UserLambdaValidationException as e:
        return {"error": True,
                "success": False,
                "message": "Email already exists",
                "data": None}

    except Exception as e:
        return {"error": True,
                "success": False,
                "message": str(e),
                "data": None}

    return {"error": False,
            "success": True,
            "message": "Please confirm your signup, \
                        check Email for validation code",
            "data": None}


def signup_confirmation(event, context=None):
    client = boto3.client('cognito-idp')
    try:
        username = event['user']
        code = event['code']
        response = client.confirm_sign_up(
            ClientId=CLIENT_ID,
            SecretHash=get_secret_hash(username),
            Username=username,
            ConfirmationCode=code,
            ForceAliasCreation=False,
        )
    except client.exceptions.UserNotFoundException:
        return {"error": True, "success": False, "message": "Username doesnt exists"}
    except client.exceptions.CodeMismatchException:
        return {"error": True, "success": False, "message": "Invalid Verification code"}

    except client.exceptions.NotAuthorizedException:
        return {"error": True, "success": False, "message": "User is already confirmed"}

    except Exception as e:
        return {"error": True, "success": False, "message": f"Unknown error {e.__str__()} "}

    return {"error": False, "success": True}


def resend_verification_code(event):
    client = boto3.client('cognito-idp')
    try:
        username = event['user']
        user_details = client.admin_get_user(Username=username, UserPoolId=USER_POOL_ID)
        if user_details["UserStatus"] == 'CONFIRMED':
            return {"error": True, "success": False, "message": "User is already confirmed"}
        response = client.resend_confirmation_code(
            ClientId=CLIENT_ID,
            SecretHash=get_secret_hash(username),
            Username=username,
        )
    except client.exceptions.UserNotFoundException:
        return {"error": True, "success": False, "message": "Username doesnt exists"}

    except client.exceptions.InvalidParameterException:
        return {"error": True, "success": False, "message": "User is already confirmed"}

    except Exception as e:
        return {"error": True, "success": False, "message": f"Unknown error {e.__str__()} "}

    return {"error": False, "success": True}


def forgot_password(event, context=None):
    client = boto3.client('cognito-idp')
    try:
        username = event['username']
        client.admin_get_user(Username=username, UserPoolId=USER_POOL_ID)
        username = event['username']
        response = client.forgot_password(
            ClientId=CLIENT_ID,
            SecretHash=get_secret_hash(username),
            Username=username,

        )
    except client.exceptions.UserNotFoundException:
        return {"error": True,
                "data": None,
                "success": False,
                "message": "Username doesnt exists"}

    except client.exceptions.InvalidParameterException:
        return {"error": True,
                "success": False,
                "data": None,
                "message": f"User {username} is not confirmed yet"}

    except Exception as e:
        return {"error": True,
                "success": False,
                "data": None,
                "message": f"Uknown    error {e.__str__()} "}

    return {
        "error": False,
        "success": True,
        "message": f"Please check your Registered email id for validation code",
        "data": None}


def confirm_forgot_password(event, context=None):
    client = boto3.client('cognito-idp')
    try:
        username = event['username']
        password = event['password']
        code = event['code']
        client.confirm_forgot_password(
            ClientId=CLIENT_ID,
            SecretHash=get_secret_hash(username),
            Username=username,
            ConfirmationCode=code,
            Password=password,
        )
    except client.exceptions.UserNotFoundException as e:
        return {"error": True,
                "success": False,
                "data": None,
                "message": "Username doesnt exists"}

    except client.exceptions.CodeMismatchException as e:
        return {"error": True,
                "success": False,
                "data": None,
                "message": "Invalid Verification code"}

    except client.exceptions.NotAuthorizedException as e:
        return {"error": True,
                "success": False,
                "data": None,
                "message": "User is already confirmed"}

    except Exception as e:
        return {"error": True,
                "success": False,
                "data": None,
                "message": f"Unknown error {e.__str__()} "}

    return {"error": False,
            "success": True,
            "message": f"Password has been changed successfully",
            "data": None}


def initiate_auth(client, username, password):
    secret_hash = get_secret_hash(username)
    try:
        resp = client.admin_initiate_auth(
            UserPoolId=USER_POOL_ID,
            ClientId=CLIENT_ID,
            AuthFlow='ADMIN_NO_SRP_AUTH',
            AuthParameters={
                'USERNAME': username,
                'SECRET_HASH': secret_hash,
                'PASSWORD': password,
            },
            ClientMetadata={
                'username': username,
                'password': password,
            })
    except client.exceptions.NotAuthorizedException:
        return None, "The username or password is incorrect"
    except client.exceptions.UserNotConfirmedException:
        return None, "User is not confirmed"
    except Exception as e:
        return None, e.__str__()
    return resp, None


def get_refreshed_tokens(username, refresh_token):
    client = boto3.client('cognito-idp')
    secret_hash = get_secret_hash(username)
    try:
        resp = client.admin_initiate_auth(
            UserPoolId=USER_POOL_ID,
            ClientId=CLIENT_ID,
            AuthFlow='REFRESH_TOKEN_AUTH',
            AuthParameters={
                'USERNAME': username,
                'REFRESH_TOKEN': refresh_token,
                'SECRET_HASH': secret_hash
            },
            ClientMetadata={
                'username': username
            })
        cookie_data_to_be_stored = get_cookie_data_to_be_stored(client, resp)
        cookie_data_to_be_stored["refresh_token"] = refresh_token
        cookie_data_to_be_stored["expires_in"] = \
            datetime.datetime.now() + datetime.timedelta(seconds=cookie_data_to_be_stored["expires_in"])
    except client.exceptions.NotAuthorizedException:
        return None, "The username or password is incorrect"
    except client.exceptions.UserNotConfirmedException:
        return None, "User is not confirmed"
    except Exception as e:
        return None, e.__str__()
    return cookie_data_to_be_stored


def get_cookie_data_to_be_stored(client, resp):
    userdetails = client.get_user(AccessToken=resp["AuthenticationResult"]["AccessToken"])["UserAttributes"]
    userdetails = {userattribute["Name"]: userattribute["Value"] for userattribute in userdetails}
    data = {
        "id_token": resp["AuthenticationResult"]["IdToken"],
        "expires_in": resp["AuthenticationResult"]["ExpiresIn"],
    }
    if resp["AuthenticationResult"].get("RefreshToken"):
        data["refresh_token"] = resp["AuthenticationResult"]["RefreshToken"]
    data.update(**userdetails)
    return data


def signin(event, context=None):
    client = boto3.client('cognito-idp')

    username, password = event.get("email"), event.get("password")
    resp, msg = initiate_auth(client, username, password)
    if msg is not None:
        return {'message': msg,
                "error": True, "success": False, "data": None}
    if resp.get("AuthenticationResult"):
        data = get_cookie_data_to_be_stored(client, resp)
        return {'message': "success",
                "error": False,
                "success": True,
                "data": data}
    else:  # this code block is relevant only when MFA is enabled
        return {"error": True,
                "success": False,
                "data": None, "message": None}
