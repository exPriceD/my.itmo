REGISTER_DATA = {'login': str, 'password': str, 'email': str, 'name': str}
LOGIN_DATA = {'login': str, 'password': str}


def check_register_data(data: dict):
    register_keys = data.keys()
    if not all(isinstance(data[key], REGISTER_DATA[key]) for key in register_keys):
        return False
    if not all(key in REGISTER_DATA and len(register_keys) == len(REGISTER_DATA) for key in register_keys):
        return False
    return True


def check_login_data(data: dict):
    login_keys = data.keys()
    if not all(isinstance(data[key], LOGIN_DATA[key]) for key in login_keys):
        return False
    if not all(key in LOGIN_DATA and len(login_keys) == len(LOGIN_DATA) for key in login_keys):
        return False
    return True

def check_send_message_data(data: dict):
    pass