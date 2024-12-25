import http.client
import json

conn = http.client.HTTPSConnection("e5gn5r.api.infobip.com")
payload = json.dumps({
    "messages": [
        {
            "destinations": [{"to":"84868656710"}],
            "from": "ServiceSMS",
            "text": "Congratulations on sending your first message. Go ahead and check the delivery report in the next step."
        }
    ]
})
headers = {
    'Authorization': 'App a83065637909ae0131bf27dbf29a6b74-2cd014b4-4bfd-496d-8abe-9d8e10d967f1',
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}
conn.request("POST", "/sms/2/text/advanced", payload, headers)
res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))