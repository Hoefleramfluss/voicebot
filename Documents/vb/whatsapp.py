from twilio.rest import Client

account_sid = 'AC3277cce33496a14e2ab2055f7a2c52fa'
auth_token = '[AuthToken]'
client = Client(account_sid, auth_token)

message = client.messages.create(
  from_='whatsapp:+14155238886',
  content_sid='HXb5b62575e6e4ff6129ad7c8efe1f983e',
  content_variables='{"1":"12/1","2":"3pm"}',
  to='whatsapp:+436641478060'
)

print(message.sid)