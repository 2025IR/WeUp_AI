from config import ROLE_CHANGE_URL, TODO_CREATE_URL, MEETING_CREATE_URL, MEETING_SAVE_URL

DISPATCH_TABLE = {
    "change_role": {
        "exec": {
            "type": "http",                       
            "method": "POST",
            "url": ROLE_CHANGE_URL,
            "mapping": {                           
                "projectId": "body.projectId",
                "userName": "body.userName",
                "roleName": "body.roleName"
            },
        }
    },
    "todo_create": {
        "exec": {
            "type": "http",
            "method": "POST",
            "url": TODO_CREATE_URL,
            "mapping": {
                "projectId": "body.projectId",
                "todoName":      "body.todoName",
                "startDate":        "body.startDate"
            },
        }
    },
    "meeting_chat": {
        "exec": {
            "type": "http",
            "method": "POST",
            "url": MEETING_CREATE_URL,
            "mapping": {
                "chatRoomId": "body.chatRoomId",
                "startTime": "body.startTime",
                "endTime": "body.endTime"
            },
        }
    },
    "meeting_save": {
        "exec": {
            "type": "http",
            "method": "POST",
            "url": MEETING_SAVE_URL,
            "mapping": {
                "projectId": "body.projectId",
                "title": "body.title",
                "contents": "body.contents"
            }
        }
    },
}