import re
import requests
import time
import json
import os
import ad

class Campaign:
    # @var Ad[] ads
    ads = []
    name = ''
    budget = 0
    money_format = re.compile('^([1-9][0-9]*|0)(\.[0-9]{2})?$')
    token = ''
    acct_id = ''
    campaign_group_id = 0
    def __init__(self, token, acct_id):
        self.token = token
        self.acct_id = acct_id

    def publish(self):
        # if self.campaign_group_id == 0:
        #     self.get_campaign_group_id()
        current_time = int(time.time()) #needed in order to code for known upcoming breaking changes
        campaign_id = self.get_campaign_id(current_time)
        # campaign_id = 6016406949638
        print "Use the campaign id "+str(campaign_id)+" to look up details about these ads"
    #     Now create the batch request for the ad group and any creatives
        if len(self.ads) > 0:
            batch = []
            images = {}
            files = {}
            data = {'access_token':self.token}
            # start by creating the image entries
            for ad in self.ads:
                images[ad.image] = ad.image
            image_num = 0
            for image in images:
                file, fileExtension = os.path.splitext(image)
                fileName = image.split('/')[-1]
                response = requests.post("https://graph.facebook.com/act_"+self.acct_id+"/adimages",
                          files={"image"+str(image_num)+fileExtension:open(image)}, data={"access_token":self.token})\
                    .json()
                images[image] = response['images'][fileName]['hash']
                image_num += 1
            for image in images:
                files[images[image]] = open(image, 'rb')
        #     Now create the creatives

            for ad in self.ads:
                creative = {"method":"POST", "relative_url": "act_"+self.acct_id+"/adgroups","redownload":True,
                  "body": ad.build_api_request_body(campaign_id, images)
                 }
                batch.append(creative)
            data['batch'] = json.dumps(batch)

            # print data
            response = requests.post('https://graph.facebook.com', data=data)
            print response.text
        else:
            print "No ads created. Campaign Id is "+str(campaign_id)
    # this function creates a new ad campaign id to be used in the batch request setting up the ad groups and creatives
    def get_campaign_id(self, time):
        if time >= 1397001600:
            status = 'PAUSED' # after April 9 (aka 1397001600) the API will require the value 'PAUSED' or 'ACTIVE'
        else:
            status = 2
        data = {'name':self.name, 'campaign_status':status, 'access_token':self.token, 'daily_budget': int(self.budget*100)}
        if self.campaign_group_id != 0: # include the campaign_group_id only if it's present
            data['campaign_group_id'] = self.campaign_group_id
        #     make the graphs api request
        response = requests.post('https://graph.facebook.com/act_' + self.acct_id + '/adcampaigns', data).json()
        if u'error' in response:
            print "Cannot create new ad campaign group. Error: " + response[u'error'][u'message']
            exit(0)
        if u'id' not in response:
            print "id not found in API response"
            print response
            exit(0)
        return response[u'id']
    # currently this code isn't called, but with the proper access rights, it should create a group campaign id to be
    # used when creating ad campaigns
    def get_campaign_group_id(self):
        data = {'name':self.name, 'campaign_group_status':'PAUSED', 'access_token':self.token}
        response = requests.post('https://graph.facebook.com/act_' + self.acct_id + '/adcampaign_groups', data).json()
        if u'error' in response:
            print "Cannot create new ad campaign group. Error: " + response[u'error'][u'message']
            exit(0)
        if u'id' not in response:
            print "id not found in API response"
            print response
            exit(0)
        new_campaign_id = response[u'id']
        self.campaign_group_id = new_campaign_id



def get_campaign(token, acct_id):
    campaign1 = Campaign(token, acct_id)
    # prompt = 'If you have an existing ad campaign group id you want to reuse, enter it here. Leave this input empty' \
    # ' to have the application create a new id for you automatically: '
    # campaign_group_id = raw_input(prompt)
    # while campaign_group_id != '' and campaign_group_id.isDigit() == False:
    #     campaign_group_id = raw_input('please enter the campaign_group_id (a number) or leave this field empty: ')
    # if campaign_group_id != '':
    #     campaign1.campaign_group_id = campaign_group_id

    prompt = 'If you have an existing ad campaign id you want to reuse, enter it here. Leave this input empty' \
        ' to have the application create a new id for you automatically: '
    campaign_id = raw_input(prompt)
    while campaign_id != '' and campaign_id.isDigit() == False:
        campaign_id = raw_input('please enter the campaign_id (a number) or leave this field empty: ')
    if campaign_id != '':
        campaign1.campaign_id = campaign_id
    else:
        name = raw_input('Enter a campaign name: ')
        while name == '':
            print "The title is not allowed to be blank."
            name = raw_input('Enter a campaign name: ')
        campaign1.name = name
        budget = raw_input('Enter a daily budget: $')
        match = campaign1.money_format.match(budget)
        while match == None:
            print 'Please enter the budget as a number like 123 or 123.45'
            budget = raw_input('Enter a daily budget: $')
            match = campaign1.money_format.match(budget)
        campaign1.budget = float(match.group(0))
    # add the ads

    ans = raw_input("Do you want to create any ads? (y/n): ")
    while ans != 'y' and ans != 'n':
        print "please enter either y or n"
        ans = raw_input("Do you want to create any ads? (y/n): ")

    num_ads = 0
    ads = []
    if ans == 'y':
        num_ads = num_ads + 1
        ad1 = ad.get_ad_details(num_ads, token)
        ads.append(ad1)
        while num_ads < 5:
            ans = raw_input('Enter another ad? (y/n): ')

            if ans == 'y':
                num_ads = num_ads + 1
                ad1 = ad.get_ad_details(num_ads, token)
                ads.append(ad1)
            elif ans == 'n':
                break
            else :
                print "please enter either y or n"
        campaign1.ads = ads
    return campaign1
