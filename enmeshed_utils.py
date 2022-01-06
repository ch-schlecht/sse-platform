import requests
import json

test_json = '''{
               "result":{
                  "messages":[
                     {
                        "id":"MSGfee2RFLiu9eAHtOBX"
                     },
                     {
                        "id":"MSGzCyQG611JhaLbWyGn"
                     }
                  ],
                  "relationships":[
                     {
                        "id":"123",
                        "changes":
                           {
                              "id":"changes_123"
                           }

                     },
                     {
                        "id":"456",
                        "changes":
                           {
                              "id":"changes_456"
                           }

                     }
                  ]
               }
            }'''

x_api_key = 'XZhCHVQlUk'

standard_header = {'x-api-key' : x_api_key}
standard_url = 'http://skm.sc.uni-leipzig.de:8090'

def test_get():
    headers = {'x-api-key':'XZhCHVQlUk'}
    r = requests.get('http://show-et-skm-1.sc.uni-leipzig.de:8090/api/v1/Messages',headers=headers)


def post_syncs():
    id_REL = []
    id_RCH = []

    id_dict = {}

    r = requests.post(standard_url + "/api/v1/Account/Sync", headers=standard_header)
    result = json.loads(r.text)
    #result = json.loads(test_json)

    if len(result["result"]["relationships"]) == 0:
        print("No relationships to accept!")
    else:
        for i in result["result"]["relationships"]:
            if i["id"] not in id_dict.keys():
                id_dict[i["id"]] = []
            print(id_dict)
            if len(i["changes"]) != 0:
                for change in i["changes"]:
                    id_dict[i["id"]].append(change["id"])

    # Todo messages -> call read_messages

    return id_dict

def accept_changes(id_dict):
    id_new_users = []

    data = {}
    data["content"] = {}

    for key in id_dict.keys():
        for entry in id_dict[key]:
            print("Accept Changes for: PUT /api/v1/Relationships/%s/Changes/%s/Accept" % (key, entry))
            r = requests.put(standard_url + "/api/v1/Relationships/{0}/Changes/{1}/Accept".format(key, entry), headers=standard_header, json=data)
            print(r.text)
            results = json.loads(r.text)

            id_new_users.append(results["result"]["peer"])
    return id_new_users
    # Todo Return id of profil, where relationship request was accepted


def send_message_to_user(subject, message, recipients):
    data = {}

    data["recipients"] = recipients
    data["content"] = {}
    data["content"]["@type"] = "Mail"
    data["content"]["to"] = recipients
    data["content"]["subject"] = subject
    data["content"]["body"] = message

    r = requests.post(standard_url + "/api/v1/Messages", headers=standard_header, json=data)
    print(r.text)

def receiving_message():
    pass

def get_Users():
    users = {}
    r = requests.get(standard_url + "/api/v1/Relationships", headers=standard_header)
    result = json.loads(r.text)
    for relationship in result["result"]:
        if relationship["peer"] not in users.keys():
            users[relationship["peer"]] = {}
        for key in relationship["changes"][0]["request"]["content"]["attributes"].keys():
            users[relationship["peer"]][key] = relationship["changes"][0]["request"]["content"]["attributes"][key]["value"]

    print(users)
    return users

def match_enmeshed(current_user_mail, enmeshed_user_dict):
    print("Search match for %s" % current_user_mail)
    for id in enmeshed_user_dict.keys():
        if enmeshed_user_dict[id]["Comm.email"].strip() == current_user_mail:
            print("Match found %s" % (current_user_mail))
            enmeshed_user_dict[id]["id"] = id
            return enmeshed_user_dict[id]
        else:
            print("No match found for %s" % current_user_mail )


def main():
    #x =post_syncs()
    #print(x)
    #accept_changes(x)
    #send_message_to_user("Hallo Subject", "Hallo message", ["id1JzYMBWvXwUeD8GCCFAcLytc3dRTyxUZhu", "id1H4gYDLQDYQmNEfGvgtgajKUmVq48nDtgF"])
    f = get_Users()
    match_enmeshed("sl74byra@studserv.uni-leipzig.de ",f)

main()
