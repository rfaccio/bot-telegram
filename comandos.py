# This Python file uses the following encoding: utf-8

# Bucket
import os
import cloudstorage as gcs
from google.appengine.api import app_identity

import StringIO
import json
import logging
import random
import urllib
import urllib2
import locale
import sys
import unicodedata
import config

def get_bucket_name():
    bucket_name = os.environ.get('BUCKET_NAME',
                                    app_identity.get_default_gcs_bucket_name())
    return bucket_name

file_path = '/' + get_bucket_name() + '/'
arquivo_chamada = file_path + 'chamada.txt'

#Envia o texto de resposta para o chat
def reply(base_url,chat_id, msg=None, img=None):
    if msg:
        resp = urllib2.urlopen(
            base_url + 'sendMessage', urllib.urlencode({
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
    chamada = []
    try:
        if not file_exists(filepath):
            write_retry_params = gcs.RetryParams(backoff_factor=1.1)
            with gcs.open(filepath, 'w', content_type='text/plain', retry_params=write_retry_params) as write_to_file:
                write_to_file.write('')
            
            logging.info('Chamada criada')
            return True, chamada
        else:
            logging.info('Chamada ja existe')
            with gcs.open(filepath) as opened_file:
                for line in opened_file:
                    line = line.decode('utf-8')
                    chamada.append(line.rstrip())
            return True, chamada          
    except Exception as e:
        logging.exception(e)
        return False, chamada

def add_pessoa(pessoa):
    chamada = abre_data('chamada')
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
            
            return pessoa + ' adicionadx com sucesso!'

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
    check1 = check2 = ''

    if not cria_chamada(arquivo_chamada):
        check1 = 'Erro ao criar ou abrir a chamada'
    if len(abre_data('chamada')) == 0:
        check2 = 'Cadastrar alguem na chamada'
    return check1, check2