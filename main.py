import StringIO
import json
import logging
import random
import urllib
import urllib2
import locale
import sys
import unicodedata

# for sending images
from PIL import Image
import multipart

# standard app engine imports
from google.appengine.api import urlfetch
from google.appengine.ext import ndb
import webapp2

# Bucket
import os
import cloudstorage as gcs
from google.appengine.api import app_identity

import config

my_default_retry_params = gcs.RetryParams(initial_delay=0.2,
                                          max_delay=5.0,
                                          backoff_factor=2,
                                          max_retry_period=15)
gcs.set_default_retry_params(my_default_retry_params)

#token definido em arquivo config.py
TOKEN = config.botToken

#
BASE_URL = BASE_URL = 'https://api.telegram.org/bot' + TOKEN + '/'

class EnableStatus(ndb.Model):
    # key name: str(chat_id)
    enabled = ndb.BooleanProperty(indexed=False, default=False)

def setEnabled(chat_id, yes):
    es = EnableStatus.get_or_insert(str(chat_id))
    es.enabled = yes
    es.put()

def getEnabled(chat_id):
    es = EnableStatus.get_by_id(str(chat_id))
    if es:
        return es.enabled
    return False

class SetBucket(webapp2.RequestHandler):
    def get(self):
        bucket_name = os.environ.get('BUCKET_NAME',
                                    app_identity.get_default_gcs_bucket_name())
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write('Demo GCS Application running from Version ' + 
                            os.environ['CURRENT_VERSION_ID'] + '\n')
        self.response.write('Using bucket name: ' + bucket_name + '\n\n')
        
        bucket = '/' + bucket_name
        filename = bucket + '/data_greg.txt'
        self.tmp_filenames_to_clean_up = []

        try:
            self.read_file(filename)
            self.response.write('\n\n')
        
        except Exception as e:
            logging.exception(e)
            self.response.write('\n\nThere was an error running the demo! '
                                'Please check the logs for more details.\n')
        
        def read_file(self, filename):

            lista = []

            with gcs.open(filename) as gcs_file:
                for line in gcs_file:
                    lista.append(line.rstrip())
            
            r = map(str, lista)
            vomit = '\n'.join(r)
            self.response.write(vomit)

class MeHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL +
                                                                 'getMe'))))


class GetUpdatesHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        self.response.write(
            json.dumps(json.load(urllib2.urlopen(BASE_URL + 'getUpdates'))))


class SetWebhookHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        url = self.request.get('url')
        if url:
            self.response.write(
                json.dumps(json.load(urllib2.urlopen(
                    BASE_URL + 'setWebhook', urllib.urlencode({'url': url})))))

class WebhookHandler(webapp2.RequestHandler):
    def post(self):
        urlfetch.set_default_fetch_deadline(60)
        body = json.loads(self.request.body)
        logging.info('request body:')
        logging.info(body)
        self.response.write(json.dumps(body))

        update_id = body['update_id']
        message = body['message']
        message_id = message.get('message_id')
        date = message.get('date')
        text = message.get('text')
        fr = message.get('from')
        chat = message['chat']
        chat_id = chat['id']

        file_path = '/dale-bot.appspot.com/data_'

        frases = []

        if not text:
            logging.info('no text')
            return        
        
        #Envia o texto de resposta para o chat
        def reply(msg=None, img=None):
            if msg:
                resp = urllib2.urlopen(
                    BASE_URL + 'sendMessage', urllib.urlencode({
                        'chat_id': str(chat_id),
                        'text': msg.encode('utf-8'),
                    })
                ).read()
            elif img:
                #TODO
                logging.error('img not yet supported')
                resp = None
            else:
                logging.error('no msg specified')
                resp = None
            
            logging.info('send response:')
            logging.info(resp)

        if text.startswith('/'):
            #remove sufixo do bot do telegram "@NOMEDOBOT"
            command = text.lower().split("@")[0]

            #extrai o nome da pessoa
            command = command.split('/')[1]

            #Liga e desliga o bot
            if command == 'start':
                reply('Acordei')
                setEnabled(chat_id, True)
            elif command == 'stop':
                reply('Dormi')
                setEnabled(chat_id, False)
            
            
            elif '_' in command:
                pessoa, subcomando = command.split('_', 1)

                filename = file_path + pessoa + '.txt'

                with gcs.open(filename) as open_file:
                    for line in open_file:
                        line = line.decode('utf-8')
                        frases.append(line.rstrip())

                if subcomando.startswith('add'):
                    #
                    texto = subcomando.split(' ')[1]
                    frases.append(texto)

                    try:
                        write_retry_params = gcs.RetryParams(backoff_factor=1.1)
                        with gcs.open(filename, 'w', content_type='text/plain', retry_params=write_retry_params) as write_to_file:
                            for line in frases:
                                write_to_file.write("%s\n" % (line.encode('utf-8')))
                        reply('Agora eu sei falar isso seu otario')

                    except Exception as e:
                        logging.exception(e)
                        reply('\n\nDeu um pau no seu programinha, bro')

                elif subcomando.startswith('vomit'):
                    r = map(unicode, frases)
                    en_r = [unicode(r.index(x) + 1) + ': ' + x for x in r]
                    vomit = '\n'.join(en_r)
                
                    reply(vomit)

            elif ' ' in command:
                pessoa, numero = command.split(' ', 1)
                filename = file_path + pessoa + '.txt'

                with gcs.open(filename) as open_file:
                    for line in open_file:
                        line = line.decode('utf-8')
                        frases.append(line.rstrip())
                
                tam = len(frases)
                i = int(numero) - 1
                if 0 <= i < tam:
                    reply(frases[i])                

            else:
                pessoa = command
                filename = file_path + pessoa + '.txt'

                with gcs.open(filename) as open_file:
                    for line in open_file:
                        line = line.decode('utf-8')
                        frases.append(line.rstrip())
                
                tam = len(frases)
                base = random.randint(0, tam)
                reply(frases[base])

app = webapp2.WSGIApplication([
    ('/me', MeHandler),
    ('/updates', GetUpdatesHandler),
    ('/set_webhook', SetWebhookHandler),
    ('/webhook', WebhookHandler),
    ('/bucket', SetBucket),
], debug=True)