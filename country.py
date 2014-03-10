import requests
import re


class Country:
    label = ''
    code = ''
    def __init__(self, country_details):
        self.label = country_details[u'name']
        self.code = country_details[u'country_code']




def get_countries(token):
    campaign_countries = {}
    add_another = 'y'
    while add_another == 'y':
        if campaign_countries == {}:
            country_name = raw_input('Enter the name of a country (at least 1 is required): ')
        else:
            country_name = raw_input('Enter the name of a country, or type "None" to continue without making a selection: ')
        if campaign_countries != {} and country_name == 'None':
            break
        elif country_name == '':
            print 'Empty response. If you do not want to enter another country, enter "None" instead.'
            continue
        else:
            r = requests.get('https://graph.facebook.com/search?type=adcountry&q='+country_name+'&access_token='+token)
            if r.status_code != requests.codes.ok: # if there's an error, print it to the console and exit
                print "Lookup failed - " + r.json()[u'error']
                exit(1)
            result = r.json()
            countries = []
            if len(result['data']) > 0:
                for country_detail in result['data']:
                    if country_detail[u'name'] not in campaign_countries:
                        # only add countries not already selected previously
                        countries.append(Country(country_detail))
            if len(countries) == 1:
                country = countries[0]
                if country_name != country.label:
                    ans = raw_input( 'Did you mean '+country.label+'? (y/n): ' )
                    while ans != 'y' and ans != 'n':
                        print 'please enter y or n'
                        ans = raw_input( 'Did you mean '+country.label+'? (y/n): ' )
                    if ans == 'y':
                        campaign_countries[country.label] = country
                else:
                    campaign_countries[country.label] = country
            elif len(countries) > 1:
                print 'Your selection matched more than one possible country, please select from one of the options, or type "None" to re-try'
                choice = -1
                while choice == -1 and choice != 'None':
                    limit = 0
                    for country in countries:
                        limit = limit + 1
                        print '['+str(limit)+'] ' + country.label
                    input = raw_input('[1-'+str(limit)+']: ')
                    if re.match('^[0-9]+$', input) and int(input) <= limit:
                        choice = int(input)
                    elif input == 'None':
                        choice = 'None'
                    else:
                        print 'Not a valid input, please enter a number between 0 and '+str(limit)+' or type "None" to re-try'
                if choice == 'None':
                    continue
                else:
                    campaign_countries[countries[choice-1].label] = countries[choice-1]
            else:
                if len(result['data']) == 0:
                    print 'Not a recognized country, please try again.'
                else:
                    print 'No further countries match that choice, please try again.'
                continue
        if len(campaign_countries) < 25:
            add_another = raw_input('Add another country? (y/n): ')
            while add_another != 'y' and add_another != 'n':
                print 'Please enter y or n'
                add_another = raw_input('Add another country? (y/n): ')
        else:
            break
    return campaign_countries
