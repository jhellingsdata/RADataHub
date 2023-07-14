import requests

request = requests.get("https://ifconfig.me")

with open("/home/ec2-user/RADataHub", "w") as f:
    f.write(request.text)