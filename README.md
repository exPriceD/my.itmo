# my.itmo backend

## /register [POST]

**Request**
```JSON
{
    "login": "user1",
    "password": "password1",
    "email": "email@mail.ru",
    "name": "Богданов Максим Александрович",
    "role": "Студент",
    "course": 1,
    "faculty": "ИКТ",
    "group": "K3140"
}
```
**Response**
```JSON
{
    "status": "200",
    "user": {
        "login": "user1",
        "password": "password1",
        "name": "Богданов Максим Александрович",
        "isu": 808140,
        "role": "Студент",
        "course": 1,
        "faculty": "ИКТ",
        "group": "K3140",
        "img": "/media/users/4"
    },
    "text": "The user has been registered"
}
```

