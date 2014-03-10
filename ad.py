import os
import re
import country
import shutil


class Ad:
    image = ''
    title = ''
    body = ''
    url = ''
    cpc_budget = 0
    country_targets = []
    gender = None
    gender_map = {'m':1, 'f':2}
    #there's probably a better way to validate images in Python, I just don't know what it is
    valid_image_types = ['.jpg', '.jpeg', '.gif', '.png']
    image_prompt = "Enter an image file (jpg, jpeg, gif or png): "
    # Here I pre-compile some regular expressions, not so much for speed, but for the sake of code organization
    url_format = re.compile('^http(?:s)?\:\/\/[_a-z0-9A-Z]+(?:\.[_a-z0-9A-Z]+)+[^\s]*$')
    initial_test=re.compile('^([a-zA-Z0-9][^\^\s~_={}[\]|\\\<>]{0,19})(?:\s([a-zA-Z0-9][^\^\s~_={}[\]|\\\<>]{0,19}))*$')
    capitalization_test = re.compile('^[A-Z]{2,20}$')
    punctuation_test = re.compile('.*(\?\?|\!\!|,,|\'\'|""|\:\:|;;|[^\.]\.\.([^\.]|$)|[\.]{4}).*')

    def get_targeting_string(self):
        if self.gender is None and len(self.country_targets) == 0:
            return ""
        targeting = "&targeting={"
        if len(self.country_targets) > 0:
            targeting+='\"geo_locations\":{\"countries\":[\"'
            countries = []
            for country in self.country_targets:
                countries.append(self.country_targets[country].code)
            targeting += '\",\"'.join(countries) + '\"]}'
        if self.gender is not None:
            if len(self.country_targets) > 0: # only add the comma between countries and genders if it's needed
                targeting += ','
            targeting += '\"genders\":['+str(self.gender)+']'
        return targeting+"}"

    def build_api_request_body(self, campaign_id, images):

        body = "campaign_id="+str(campaign_id)\
            +"&bid_type=CPC&bid_info={\"clicks\":"+str(self.cpc_budget)+"}" \
             "&creative={\"title\":\""+self.title+"\"," \
                        "\"body\":\""+self.body+"\"," \
                        "\"link_url\":\""+self.url+"\"," \
                        "\"image_hash\":\""+images[self.image]+"\"}" \
             +self.get_targeting_string()+ \
             "&name="+self.title
        return body

# The following rules apply to the title and body parameters:
#
# Cannot start with punctuation
# Cannot have duplicate consecutive punctuation characters with the exception of 3 periods...
# Words cannot be greater than 20 characters in length
# Only 2 consecutive 1 character words are allowed
# Cannot consist entirely of capital letters
# Double spacing is not allowed
# The following are the limits on the fields in an ad creative:
#
# The maximum amount of characters that can be in an ad's title : 25 characters
# The maximum amount of characters that can be in an ad's body : 90 characters
# The maximum amount of characters that can be in a URL : 1024 characters
# The maximum allowable length of an individual word in an ad's text or title : 20 characters
# The minimum amount of characters that can be in an ad's title : 1 character
# The minimum amount of characters that can be in an ad's body :1 character
#
# The following characters are not allowed:
#
# IPA Symbols
# Diacritical Marks (precomposed version of a character + diacritical mark are allowed, standalone diacritical marks are
# not allowed)
# Superscript and Subscript characters with the exception of ^TM and ^SM
# The following characters \^~_={}[]|<>
def validate(string):
    match = Ad.initial_test.match(string)
    if match is None:
        # either the words are too long, have too many spaces inbetween, begin with punctuation, contain illegal chars,
        # or the string is empty
        return False
    last_word_len = 0
    next_to_last_word_len = 0
    for word in string.split(' '):
        if len(word) == 1 and last_word_len == 1 and next_to_last_word_len == 1:
            return False #can't have more than two consecutive one-letter words
        else:
            next_to_last_word_len = last_word_len
            last_word_len = len(word)
        if Ad.capitalization_test.match(word) is not None:
            return False #can't have any words in all caps
        if Ad.punctuation_test.match(word) is not None:
            # except for "..." cannot have duplicate consecutive punctuation characters
            return False
        # if re.match('.*[^\.]\.\.[^\.].*', word) is not None:
        #     return False
        #todo - once I know more about character encoding in Python, add checks for solitary diactricial marks, super-
        # and sub- scripts, IPA symbols, and explicitly allow a wider range of characters in the first character (just
        # no punctuation)
    return True

def get_ad_details(num_ads, token):
    ad = Ad()
    print 'Ad #'+str(num_ads)
    # title
    title = raw_input("Enter a title for this ad: ")
    while validate(title) == False or len(title) > 25:
        print "That title is not allowed."
        title = raw_input("Enter a title for this ad: ")
    ad.title = title
    # body
    body = raw_input('Enter the ad body: ')
    while validate(body) == False or len(body) > 90:
        print "That ad body is not allowed."
        body = raw_input('Enter the ad body: ')
    ad.body = body
    # image
    image = raw_input(Ad.image_prompt)
    hasImage = False
    fileName, fileExtension = os.path.splitext(image)
    while hasImage == False:
        while fileExtension not in Ad.valid_image_types:
            print 'That filename does not match one of the expected image file extensions'
            print fileExtension
            image = raw_input(Ad.image_prompt)
            fileName, fileExtension = os.path.splitext(image)
        # exiting this loop means the extension matches one of the valid type
        while os.path.isfile(image) == False:
            print 'That file is not readable'
            image = raw_input(Ad.image_prompt)
        # exiting this loop means the file exists, but we still need to check the extension
        fileName, fileExtension = os.path.splitext(image)
        if fileExtension in Ad.valid_image_types:
            hasImage = True
            fileName = fileName.split('/')[-1]
            if os.path.exists("tmp") == False:
                os.mkdir("tmp")
            if image != "tmp/"+fileName+fileExtension:
                shutil.copy(image,"tmp/"+fileName+fileExtension)
    ad.image = "tmp/"+fileName+fileExtension
    # url
    url = raw_input("Enter the object_url: ")
    # very basic validation
    match = Ad.url_format.match(url)
    while match == None or len(url) > 1024:
        print "Specify a valid URL"
        url = raw_input("Enter the object_url: ")
        match = Ad.url_format.match(url)
    ad.url = match.group(0)
    # budget
    cpc_budget = raw_input('Enter the CPC budget for this ad in pennies per click: ')
    while cpc_budget.isdigit() == False or int(cpc_budget) == 0:
        print 'Please enter a valid CPC budget, minimum 1'
        cpc_budget = raw_input('Enter the CPC budget for this ad in pennies per click: ')
    ad.cpc_budget = cpc_budget
    ad.country_targets = country.get_countries(token)

    # add any gender targeting
    ans = raw_input('Do you want to specify gender targeting? (y/n): ')
    while ans != 'y' and ans != 'n':
        print 'Please enter either y or n'
        ans = raw_input('Do you want to specify gender targeting? (y/n): ')
    if ans == 'y':
        gender = raw_input('Target male or female? (m/f) or "None" to cancel : ')
        while gender != 'm' and gender != 'f' and gender != 'None':
            print 'Please enter either "m", "f" or "None"'
            gender = raw_input('Target male or female? (m/f): ')
        if gender != 'None':
            ad.gender = Ad.gender_map[gender]
    return ad