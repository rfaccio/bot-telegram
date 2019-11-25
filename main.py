# This Python file uses the following encoding: utf-8

import StringIO
import json
import logging
import random
import urllib
import urllib2
import locale
import sys
import unicodedata

# standard app engine imports
from google.appengine.api import urlfetch
from google.appengine.ext import ndb
import webapp2

# Bucket
import os
import cloudstorage as gcs
from google.appengine.api import app_identity

# Funcionalidades
import config
import comandos

my_default_retry_params = gcs.RetryParams(initial_delay=0.2,
                                          max_delay=5.0,
                                          backoff_factor=2,
                                          max_retry_period=15)
gcs.set_default_retry_params(my_default_retry_params)

#token definido em arquivo config.py
TOKEN = config.Settings.get('TELEGRAM_TOKEN')
BASE_URL = 'https://api.telegram.org/bot' + TOKEN + '/'

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

class MeHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'getMe'))))


class GetUpdatesHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'getUpdates'))))


class SetWebhookHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        url = self.request.get('url')
        if url:
            self.response.write(
                json.dumps(json.load(urllib2.urlopen(BASE_URL + 'setWebhook', urllib.urlencode({'url': url})))))

class WebhookHandler(webapp2.RequestHandler):
    def post(self):
        #Envia o texto de resposta para o chat
        def reply(message=None, img=None):
            comandos.reply(BASE_URL,message,img)

        urlfetch.set_default_fetch_deadline(60)
        body = json.loads(self.request.body)
        logging.info('request body:')
        logging.info(body)
        self.response.write(json.dumps(body))

        # recupera informações da mensagem
        try:
            message = body['message']
        except:
            message = body['edited_message']

        msg = {}
        msg['text'], msg['message_id'], msg['chat_id'], msg['user_id'] = comandos.extrai_texto(message)

        if not msg['text']:
            msg['text'], msg['reply_msg_txt'], msg['sticker_id'], msg['emoji'] = comandos.extrai_reply(message)

        #inicializa algumas variáveis globais
        comandos.inicializa(BASE_URL,msg['chat_id'])
        #verifica a necessidade de criar nova chamada
        comandos.verifica_chamada(BASE_URL,msg['chat_id'])

        if not msg['text']:
            logging.info('no text')
            return
        
        comandos.send_action('typing')

        logging.info('text is: ' + msg['text'])
        if msg['text'].startswith('/'):
            msg['text'] = msg['text'].split('/')[1]
            #remove sufixo do bot do telegram "@NOMEDOBOT"
            #extrai apenas o comando            
            command = comandos.get_comando(msg['text'].lower().split("@")[0])

            #COMANDOS
            #Liga e desliga o bot
            if command == 'start':
                reply('Acordei')
                setEnabled(msg['chat_id'], True)
            elif command == 'stop':
                reply('Dormi')
                setEnabled(msg['chat_id'], False)
            #Adiciona nova pessoa à lista de chamada e cria arquivo data_PESSOA
            elif command == 'add_pessoa':
                reply(comandos.add_pessoa(msg['text']))
            #Adiciona nova frase para uma pessoa
            elif command == 'add_frase':
                reply(comandos.add_frase(**msg))
            elif command == 'del_frase':
                reply(comandos.del_frase(msg['text']))
            #Adiciona o sticker enviado como repsta ao "add_frase sticker"
            elif command == 'add_sticker':
                reply(comandos.add_sticker(**msg))
            #Envia todas as frases de uma pessoa
            elif command == 'vomit':
                reply(comandos.get_vomit(msg['text']))
            #Envia uma frase específica
            elif command == 'get_frase_numero':
                reply(comandos.get_frase_numero(msg['text']))
            #Envia uma frase aleatória
            elif command == 'random':
                reply(comandos.get_frase_random(msg['text']))
            elif command == 'hype':
                reply(comandos.get_hype(msg['text']))
            #Envia a lista de chamada
            elif command == 'chamada':
                reply(comandos.get_vomit('chamada'))
            else:
                reply('comando nao reconhecido')

app = webapp2.WSGIApplication([
    ('/me', MeHandler),
    ('/updates', GetUpdatesHandler),
    ('/set_webhook', SetWebhookHandler),
    ('/webhook', WebhookHandler),
], debug=True)