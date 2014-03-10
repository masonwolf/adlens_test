import campaign

token = '[enter a valid access token]'
acct_id = '[enter an account id]'
# create the campaign
campaign1 = campaign.get_campaign(token, acct_id)

# publish it to Facebook
campaign1.publish()