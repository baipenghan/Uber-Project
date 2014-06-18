from bottle import Bottle, response, request, route, run, debug, template
import requests, re, json, sqlite3
from datetime import datetime
from HTMLParser import HTMLParser

providers = []
provider_index = None
email_provider = None
app = Bottle()
conn = sqlite3.connect('test.db')

class TagRemover(HTMLParser):
    def __init__(self):
        self.reset()
        self.content = []
    def handle_data(self, d):
        self.content.append(d)
    def get_data(self):
        return ' '.join(self.content)

class EmailProvider():
    def __init__(self, info):
        self.info = {}
        for key, value in info.items():
            self.info[key] = value
    def send_email(to_email, to_name, from_email, from_name, subject, new_body):
        return

class Mailgun(EmailProvider):
    def send_email(self, to_email, to_name, from_email, from_name, subject, new_body):
        return requests.post('https://api.mailgun.net/v2/' + self.info['domain']+ '/messages',
            auth=("api", self.info["api_key"]),
            data={"from": "%s <%s>" % (from_name, from_email),
                "to": "%s %s" % (to_name, to_email),
                "subject": subject,
                "text": "%s" % new_body})

class Mandrill(EmailProvider):
    def send_email(self, to_email, to_name, from_email, from_name, subject, new_body):
        data={"key": self.info['api_key'],
            "message": {"text": new_body,
                "from_email": from_email,
                "from_name": from_name,
                "to": [{"email": to_email, "type": "to", "name": to_name}],
                "subject": subject}
            }
        return requests.post("https://mandrillapp.com/api/1.0/messages/send.json",
            data=json.dumps(data)
                )

def validate_input(to_email, to_name, from_email, from_name, subject, body):
    if to_email == '':
        return 'To Email is empty'
    if to_name == '':
        return 'To Name is empty'
    if from_email == '':
        return 'From Email is empty'
    if from_name == '':
        return 'From Name: is empty'
    if subject == '':
        return 'Subject: is empty'
    if body == '':
        return 'Body: is empty'

    if not re.match(r"[^@]+@[^@]+\.[^@]+", from_email):
        return 'From Email: %s is not valid' % from_email
    if not re.match(r"[^@]+@[^@]+\.[^@]+", to_email):
        return 'To Email: %s is not valid' % to_email

    return True

# If we have more than 2 email providers, we can move to the next provider
# in the list in this way, by adding 1 and mod by the size of the providers.
def switch_provider():
    global email_provider, provider_index
    provider_index = (provider_index + 1) % len(providers)
    email_provider = providers[provider_index]

def save(to_email, to_name, from_email, from_name, subject, body):
    global conn
    conn.execute("INSERT INTO email VALUES (?,?,?,?,?,?,?)", (datetime.now(), to_email, to_name, from_email, from_name, subject, body))
    conn.commit()

@app.post('/email')
def parse():
    global provider_index
    data = request.json
    to_email = data['to'].strip()
    to_name = data['to_name'].strip()
    from_email = data['from'].strip()
    from_name = data['from_name'].strip()
    subject = data['subject'].strip()
    body = data['body'].strip()
    valid_input = validate_input(to_email, to_name, from_email, from_name, subject, body)
    if valid_input != True:
        response.status = 400
        return {'content': valid_input}

    tag_remover = TagRemover()
    tag_remover.feed(body)
    new_body = tag_remover.get_data()

    save(to_email, to_name, from_email, from_name, subject, new_body)

    r = email_provider.send_email(to_email, to_name, from_email, from_name, subject, new_body)
    if r.status_code != 200:
        switch_provider()

    # print r.json()
    return

def main():
    global providers, email_provider, conn, provider_index
    host = None
    port = None
    conn.execute('create table if not exists email (time timestamp, to_email TEXT, to_name TEXT, from_email TEXT, from_name TEXT, subject TEXT, body TEXT)')

    json_file = open('configure.json')
    json_info = json.load(json_file)
    json_file.close()

    for provider in json_info:
        if provider.get('name') == 'Mandrill':
            providers.append(Mandrill(provider['info']))
        elif provider.get('name') == 'Mailgun':
            providers.append(Mailgun(provider['info']))
        elif provider.get('name') == None:
            provider_index = provider['default_index']
            host = provider['host']
            port = provider['port']
    email_provider = providers[provider_index]
    # debug(True)
    run(app, host=str(host), port=int(port))

if __name__ == '__main__':
    main()
