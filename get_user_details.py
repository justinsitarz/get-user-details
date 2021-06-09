import csv
import requests
import json
import pandas as pd
import sys

api_key = '8790b795-e6cd-4f5b-9515-5592639c5ced'
user_data_csv = './user-list.csv' # set this to your desired path or leave the same to generate csv in same directory
api_headers = {'Content-Type': 'application/json','Authorization':'GenieKey ' + api_key}
get_user_url = "https://api.opsgenie.com/v2/users/" # set as https://api.eu.opsgenie.com/v2/users/ if account is in the EU region
expand_params = {'expand': 'contact'}


def build_user_list(api_key, url, api_headers):

    try:
        user_list_request = requests.get(url = get_user_url, headers = api_headers)
        user_list_request.raise_for_status()
    except requests.exceptions.RequestException as e:  # This is the correct syntax
        raise SystemExit(e)

    user_json = json.loads(user_list_request.text) 
    users = []
    
    for user in user_json['data']:
        if user['role']['name'] != "Stakeholder":
            users.append(user['username'])

    while 'next' in user_json['paging']:
        next_url = str(user_json['paging']['next'])
        user_list_request = requests.get(url = next_url, headers = api_headers)
        user_json = json.loads(user_list_request.text)    
        for user in user_json['data']:
            if user['role']['name'] != "Stakeholder":
                users.append(user['username'])
    return users

def get_user_data(users):
    user_dict = {}
    count = len(users)
    print(str(count) + " users left.")
    for u in users:
        user_dict[u] = get_user_details(u)
        count -= 1
        print("User added: " + u + ", " + str(count) + " users left.")
    generate_csv(user_dict)


def get_user_details(username):
    user = {}
    user_request = requests.get(url = get_user_url + username, headers = api_headers, params = expand_params)
    user_data = json.loads(user_request.text)['data']
    user_teams = get_teams(username)
    user_schedules = get_schedules(username)
    user_escalations = get_escalations(username)

    user_contacts = user_data.get('userContacts')
    user_email = []
    user_mobile = []
    user_sms = []
    user_voice = []

    if user_contacts:

        for u in user_contacts:
            if u['contactMethod'] == 'email':
                user_email.append(u['to'])
            if u['contactMethod'] == 'mobile':
                user_mobile.append(u['to'])
            if u['contactMethod'] == 'sms':
                user_sms.append(u['to'])
            if u['contactMethod'] == 'voice':
                user_voice.append(u['to'])

    user['full_name'] = user_data['fullName']
    user['username'] = user_data['username']
    user['time_zone'] = user_data['timeZone']
    user['locale'] = user_data['locale']
    user['verified'] = user_data['verified']
    user['user_id'] = user_data['id']
    user['user_role'] = user_data['role']['name']
    # user['user_address'] = user_data['userAddress']
    user['created_date'] = user_data['createdAt']

    user['email'] = ', '.join(user_email)
    user['mobile'] = ', '.join(user_mobile)
    user['sms'] = ', '.join(user_sms)    
    user['voice'] = ', '.join(user_voice)
    user['teams'] = ', '.join(user_teams)
    user['schedules'] = ', '.join(user_schedules)
    user['escalations'] = ', '.join(user_escalations)
    
    return user


def get_teams(username):
    user_teams_request = requests.get(url = get_user_url + username + "/teams", headers = api_headers)
    teams = json.loads(user_teams_request.text)['data']
    teams_list = []
    for t in teams:
        teams_list.append(t['name'])
    return teams_list

def get_schedules(username):
    user_schedules_request = requests.get(url = get_user_url + username + "/schedules" , headers = api_headers)
    schedules = json.loads(user_schedules_request.text)['data']
    schedules_list = []
    for s in schedules:
        schedules_list.append(s['name'])
    return schedules_list

def get_escalations(username):
    user_escalations_request = requests.get(url = get_user_url + username + "/escalations" , headers = api_headers)
    escalations = json.loads(user_escalations_request.text)['data']
    escalations_list = []
    for e in escalations:
        escalations_list.append(e['name'])
    return escalations_list

def generate_csv(user):
    df = pd.DataFrame(user)
    df_transposed = df.transpose()
    df_transposed.to_csv(user_data_csv, sep=',', encoding='utf-8')

users = build_user_list(api_key, get_user_url, api_headers)
get_user_data(users)

