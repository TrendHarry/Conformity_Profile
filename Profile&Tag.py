import requests

null = None
true = True
false = False


class CloudConformity(object):
    __slots__ = ('region', 'apikey', 'header')

    def __init__(self, region: str, apikey: str) -> None:
        self.region = region
        self.apikey = apikey
        self.header = {
            'Content-Type': 'application/vnd.api+json',
            'Authorization': f'ApiKey {self.apikey}'
        }

    def get(self, url: str) -> dict():
        response = requests.get(url, headers=self.header)
        return eval(response.text)

    def post(self, url: str, data: str) -> None:
        response = requests.post(
            url, data=data, headers=self.header)
        print(response.text)

    def patch(self, url: str, data: str) -> None:
        response = requests.patch(url, data=data, headers=self.header)
    
    def enter_idx(self, item: str, dic: dict) -> str:
        print(f'***{item}***\t')
        i = 0
        dic_select = dict()
        for key in dic:
            i += 1
            dic_select.update({i:key})
            print(f'{i} : {key}\t')
        idx = int(input('Please enter the index you want: '))
        select_item = dic_select[idx]
        print (f'Your selection: {select_item}')
        return select_item

# user input
region = input('Which region is your conformity environment hosted in? ')
apikey = input('Enter your api key: ')

api = CloudConformity(region, apikey)

def main():
    print('1 : apply profile to accouts of selected group, add tags to each accounts')
    print('2 : show accounts with selected tag')
    idx = int(input('Please enter the index of you want: '))
    if idx == 1:
        apply_profile()
    else:
        list_tagged_accounts()


def apply_profile():
    # 1. list all groups and enter group you want
    url = f'https://conformity.{api.region}.cloudone.trendmicro.com/api/groups'
    dic = api.get(url)

    dic_group_name2id = dict()
    for data in dic['data']:
        name = data['attributes']['name']
        id = data['id']
        dic_group_name2id.update({name:id})
    group_name = api.enter_idx('group name', dic_group_name2id)

    # 2. get group details and display accounts
    url = f'https://conformity.{api.region}.cloudone.trendmicro.com/api/groups/{dic_group_name2id[group_name]}'
    dic = api.get(url)

    dic_account_name2id = dict()
    for data in dic['data'][0]['relationships']['accounts']['data']:
        id = data['id']
        url = f'https://conformity.{api.region}.cloudone.trendmicro.com/api/accounts/{id}'
        dic_accout = api.get(url)
        name = dic_accout['data']['attributes']['name']
        dic_account_name2id.update({name:id})

    print(f'***all accounts in the selected group***\t')
    i = 0
    for name in dic_account_name2id:
        i += 1
        print(f'{i} : {name}\t')

    # 3. list all profiles and enter profile you want
    url = f'https://conformity.{api.region}.cloudone.trendmicro.com/api/profiles'
    dic = api.get(url)

    dic_profile_name2id = dict()
    for data in dic['data']:
        name = data['attributes']['name']
        id = data['id']
        dic_profile_name2id.update({name:id})
    profile_name = api.enter_idx('profile name', dic_profile_name2id)

    # 4. apply profile to accounts and update account(add profile name as a tag)
    url = f'https://conformity.{api.region}.cloudone.trendmicro.com/api/profiles/{dic_profile_name2id[profile_name]}/apply'

    ls_account_ids = list()
    data = '{\
            "meta":{\
                    "accountIds": [],\
                    "types": ["rule"],\
                    "mode": "overwrite",\
                    "notes": "Applying profile to accounts",\
                    "include": {\
                                    "exceptions": false\
                    }\
            }\
        }'
    for name in dic_account_name2id:
        ls_account_ids.append(dic_account_name2id[name])
    dic = eval(data)
    dic['meta']['accountIds']= ls_account_ids
    data = str(dic)
    data = data[:-8] + 'f' + data[-7:]
    api.post(url, data)
    profile_name = 'Profile' + profile_name

    for name in dic_account_name2id:
        # get account details
        url = f'https://conformity.{region}.cloudone.trendmicro.com/api/accounts/{dic_account_name2id[name]}'
        dic = api.get(url)
        name = dic['data']['attributes']['name']
        tags = dic['data']['attributes']['tags']

        # update account
        if profile_name not in tags:
            tags.append(profile_name)
            url = f'https://conformity.{region}.cloudone.trendmicro.com/api/accounts/{dic_account_name2id[name]}'
            data ='{\
                                    "data": {\
                                        "attributes": {\
                                            "name": "",\
                                            "tags": []\
                                        }\
                                    }\
                                }'
            dic = eval(data)
            dic['data']['attributes']['name'] = name
            dic['data']['attributes']['tags'] = tags
            data = str(dic)
            api.patch(url, data=data)


# list all tag, and display account names with selected tag.
def list_tagged_accounts():
    url = f'https://conformity.{api.region}.cloudone.trendmicro.com/api/accounts'
    dic = api.get(url)

    dic_tags2name = dict()
    print('***account_name***\t ***tags***\t')
    for account in dic['data']:
        print('{%s}\t {%s}\t' % (account['attributes']['name'], account['attributes']['tags']))
        tags = account['attributes']['tags']
        account_name = account['attributes']['name']
        for tag in tags:
            dic_tags2name.setdefault(tag,[]).append(account_name)

    tag = api.enter_idx('tag', dic_tags2name)
    if tag in dic_tags2name:
        print(dic_tags2name[tag])
    else:
        print('No account has this tag')


if __name__ == '__main__':
    main()