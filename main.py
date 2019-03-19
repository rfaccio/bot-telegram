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

import config

my_default_retry_params = gcs.RetryParams(initial_delay=0.2,
                                          max_delay=5.0,
                                          backoff_factor=2,
                                          max_retry_period=15)
gcs.set_default_retry_params(my_default_retry_params)

#token definido em arquivo config.py
TOKEN = config.TOKEN

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
        bucket_name = os.environ.get('BUCKET_NAME',
                                    app_identity.get_default_gcs_bucket_name())
        update_id = body['update_id']
        message = body['message']
        message_id = message.get('message_id')
        date = message.get('date')
        text = message.get('text')
        fr = message.get('from')
        chat = message['chat']
        chat_id = chat['id']        
        chamada = []        
        frases = []
        file_path = '/' + bucket_name + '/'        
        arquivo_chamada = file_path + 'chamada.txt'  

        if not text:
            logging.info('no text')
            return
        
        def get_datafilename(pessoa):
            
            if pessoa == 'chamada':
                return arquivo_chamada
            else:
                return file_path + 'data_' + pessoa + '.txt'

        def file_exists(gcs_file):
            try:
                gcs.stat(gcs_file)
                logging.info('arquivo existe')
                return True
            except Exception as e:
                logging.info('arquivo nao existe')
                return False
        
        def cria_chamada(filepath):
            try:
                if not file_exists(filepath):
                    write_retry_params = gcs.RetryParams(backoff_factor=1.1)
                    with gcs.open(filepath, 'w', content_type='text/plain', retry_params=write_retry_params) as write_to_file:
                        write_to_file.write('')
                    
                    logging.info('Chamada criada')
                    return True
                else:
                    logging.info('Chamada ja existe')
                    with gcs.open(filepath) as opened_file:
                        for line in opened_file:
                            line = line.decode('utf-8')
                            chamada.append(line.rstrip())
                    return True          
            except Exception as e:
                logging.exception(e)
                return False

        def add_pessoa(pessoa):
            
            logging.info('Adicionando nova pessoa: ' + pessoa)
            if len(pessoa) >= 1 and not pessoa in chamada:
                #adiciona
                chamada.append(pessoa)
                try:
                    write_retry_params = gcs.RetryParams(backoff_factor=1.1)
                    with gcs.open(arquivo_chamada, 'w', content_type='text/plain', retry_params=write_retry_params) as write_to_file:
                        for line in chamada:
                            write_to_file.write("%s\n" % (line.encode('utf-8')))

                    with gcs.open(get_datafilename(pessoa), 'w', content_type='text/plain', retry_params=write_retry_params) as novo:
                        novo.write('')
                    
                    return pessoa + 'adicionadx'

                except Exception as e:
                    logging.exception(e)
                    return 'Deu um pau no seu programinha, bro'
            else:
                return 'Pessoa ja existe ou nome invalido'

        def abre_data(pessoa):
            retorno = []
            with gcs.open(get_datafilename(pessoa)) as open_file:
                for line in open_file:
                    line = line.decode('utf-8')
                    retorno.append(line.rstrip())
            return retorno
        
        def adiciona_frase(pessoa, texto):
            data = abre_data(pessoa)
            data.append(texto)
            try:
                write_retry_params = gcs.RetryParams(backoff_factor=1.1)
                with gcs.open(get_datafilename(pessoa), 'w', content_type='text/plain', retry_params=write_retry_params) as write_to_file:
                    for line in data:
                        write_to_file.write("%s\n" % (line.encode('utf-8')))
                #reply('Agora eu sei falar isso seu otario')
                return 'Agora eu sei falar isso seu otario'
            except Exception as e:
                logging.exception(e)
                #reply('\n\nDeu um pau no seu programinha, bro')
                return '\n\nDeu um pau no seu programinha, bro'

        def get_frase_numero(pessoa, numero):
            data = abre_data(pessoa)                
            tam = len(data)
            i = int(numero) - 1
            if 0 <= i < tam:
                return data[i]
            else:
                return 'Tente outro numero amg'

        def get_frase_random(pessoa):
            data = abre_data(pessoa)            
            tam = len(data)
            base = random.randint(0, tam)
            return data[base]

        def get_vomit(pessoa):
            data = abre_data(pessoa)
            r = map(unicode, data)
            en_r = [unicode(r.index(x) + 1) + ': ' + x for x in r]
            vomit = '\n'.join(en_r)
            return vomit

        def get_comando(texto):
            comando = ''

            if texto == 'start':
                comando = 'start'
            elif texto == 'stop':
                comando = 'stop'
            elif texto.startswith('add_pessoa '):
                comando = 'add_pessoa'
            elif '_' in texto:
                subcomando = texto.split('_', 1)[1]
                if subcomando.startswith('add'):                 
                    comando = 'add_frase'
                elif subcomando.startswith('vomit'):
                    comando = 'vomit'
            elif ' ' in texto:
                comando = 'get_numero'
            elif texto == 'chamada':
                comando = 'chamada'
            else:
                comando = 'random'
            
            return comando

        def verifica_chamada():
            #verifica a necessidade de criar uma nova chamada
            if not cria_chamada(arquivo_chamada):
                reply('Erro ao criar ou abrir a chamada')            
            if len(chamada) == 0:
                reply('Cadastrar alguem na chamada')

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
            text = text.split('/')[1]
            #remove sufixo do bot do telegram "@NOMEDOBOT"
            #extrai apenas o comando            
            command = get_comando(text.lower().split("@")[0])

            verifica_chamada()
            
            #COMANDOS
            #Liga e desliga o bot
            if command == 'start':
                reply('Acordei')
                setEnabled(chat_id, True)
            elif command == 'stop':
                reply('Dormi')
                setEnabled(chat_id, False)

            elif command == 'add_pessoa':
                pessoa = text.split(' ', 1)[1]
                reply(add_pessoa(pessoa))

            elif command == 'add_frase':
                pessoa = text.split('_', 1)[0]
                texto = text.split(' ', 1)[1]
                reply(adiciona_frase(pessoa,texto))                
                    
            elif command == 'vomit':
                pessoa = text.split('_', 1)[0]                
                reply(get_vomit(pessoa))

            elif command == 'get_numero':
                pessoa, numero = text.split(' ', 1)
                reply(get_frase_numero(pessoa, numero))
            elif command == 'random':
                reply(get_frase_random(text.lower().split("@")[0]))
            else:
                reply('comando nao reconhecido')

app = webapp2.WSGIApplication([
    ('/me', MeHandler),
    ('/updates', GetUpdatesHandler),
    ('/set_webhook', SetWebhookHandler),
    ('/webhook', WebhookHandler),
    ('/bucket', SetBucket),
], debug=True)