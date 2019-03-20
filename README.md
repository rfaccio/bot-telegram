# bot-telegram

## Instalando:

1. Criar projeto no Google Cloud (cloud.google.com)
2. Copiar o nome do projeto e atualizar o arquivo app.yaml
3. Criar um bot através do BotFather no Telegram
4. Copiar o TOKEN e salvar em um arquivo config.py (adicionar config.py ao gitignore)
5. Realizar o deploy usando o Google App Engine

## Utilizando

1. Ao iniciar, será criado um arquivo "chamada.txt" que irá conter o nome dos participantes
2. É necessario adicionar ao menos 1 pessoa à lista de chamada
   
## Comandos Disponíveis
NOME = substituir pelo nome
NUMERO = substituir por um numero válido
FRASE = substituir pela frase
1. /add_pessoa NOME: adiciona uma nova pessoa à lista de chamada e cria um arquivo "data_xxx.txt", que irá conter as frases desta pessoa
   1. Ex: "/add_pessoa greg" = cria a pessoa "greg"
2. /NOME_add FRASE: irá adicionar a FRASE ao arquivo da pessoa NOME
   1. Ex: "/greg_add amo marx" = adiciona "amo marx" às frases do greg
3. /NOME: irá retornar uma frase aleatória desta pessoa NOME
   1. Ex: "/greg"
4. /NOME NUMERO: irá retornar uma frase específica da lista de frases da pessoa NOME
   1. Ex: "/greg 3" = retorna a frase n° 3 do greg
5. /NOME_vomit: irá retornar toda a lista de frases da pessoa NOME
   1. Ex: "/greg_vomit" = retorna a lista completa das frases do greg 