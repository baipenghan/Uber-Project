import requests, json
import unittest

class TestSequenceFunctions(unittest.TestCase):
    def setUp(self):
        json_file = open('configure.json')
        json_info = json.load(json_file)
        json_file.close()
        host = None
        port = None
        for provider in json_info:
            if provider.get('name') == None:
                host = provider['host']
                port = provider['port']
        self.url = "http://%s:%s/email" % (host, str(port))

    def test_invalid_email(self):
        data={
            "from": "abc@example.com",
            "from_name": "Patrick",
            "to": "AAABBBCCC",
            "to_name": "Bob",
            "body": "Hello World!",
            "subject": "Hi"}
        headers = {'content-type': 'application/json'}
        r = requests.post(self.url, data=json.dumps(data), headers=headers)
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()['content'], 'To Email: %s is not valid' % data['to'])

    def test_empty_input(self):
        data={
            "from": "   ",
            "from_name": "Patrick",
            "to": "bob@example",
            "to_name": "Bob",
            "body": "Hello World!",
            "subject": "Hi"}
        headers = {'content-type': 'application/json'}
        r = requests.post(self.url, data=json.dumps(data), headers=headers)
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()['content'], 'From Email is empty')

    def test_successful_request(self):
        data={
            "from": "patrick@example.com",
            "from_name": "Patrick",
            "to": "bob@example.com",
            "to_name": "Bob",
            "body": "Hello World!",
            "subject": "Hi"}
        headers = {'content-type': 'application/json'}
        r = requests.post(self.url, data=json.dumps(data), headers=headers)
        self.assertEqual(r.status_code, 200)

if __name__ == '__main__':
    unittest.main()
