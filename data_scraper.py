'''
Script de coleta de dados da API do Helium Network

PASSO 1: coleta dos dados sobre todos os hotspots existentes;
PASSO 2: coleta dos dados de rendimento de cada hotspot;
PASSO 3: coleta das quantidades de hotspots proximos para cada hotspot.

'''

from tqdm import tqdm
from funcoes import *

import os
import json
import requests
import numpy as np
import pandas as pd
import datetime as dt

# data de hoje para coleta de dados dependentes da data
data_hoje = str(dt.date.today())
data_hora_hoje = "%sT00:00:00Z" % data_hoje


# PASSO 1: coleta dos dados sobre os hotspots existentes --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- 1

# prints de verbose
print('Coletando dados sobre os hotspots existentes...\n')
print('\t0')

# coleta da primeira página da lista de hotspots
resposta = requests.get('https://api.helium.io/v1/hotspots')
dados = resposta.json()

# verifica se há, de fato, mais páginas
try: cursor = dados['cursor']; mais_paginas = True
except KeyError: mais_paginas = False

# lista de dicionários base
todos_hotspots = dados['data']

# print de verbose
print('\t' + str(len(todos_hotspots)))

# loop de download das páginas
while mais_paginas:

	# coleta da página em questão a partir do cursor da anterior
    resposta = requests.get('https://api.helium.io/v1/hotspots?cursor=' + cursor)
    dados = resposta.json()

    # adição dos dados da página à lista completa
    todos_hotspots += dados['data']

    # print de verbose
    print('\t' + str(len(todos_hotspots)))

    # cláusula de finalização do loop
    try: cursor = dados['cursor']
    except KeyError: break

'''
PASSO 1 finalizado, daqui sai:
	- todos_hotspots -> lista de dicionários, cada dicionário representa um hotspot
'''

# -- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- 1'


# armazenamento dos dados brutos sobre os hotspots
dados_armazentamento = {'data': todos_hotspots, 'date': data_hoje}
with open('dados/todos_hotspots_%s.json' % data_hoje, 'w') as json_file:
	json.dump(dados_armazentamento, json_file)


# PASSO 2: coleta dos dados de rendimento dos hotspots 	 --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- 2

print('\nColetando dados de rendimento dos hotspots...')

# dicionário principal
dados_brutos = list()

indice = 0
for hotspot in tqdm(todos_hotspots):
    
    # dicionário base para o hotspot
	dados = dict()
	dados.update(hotspot)
	dados['age'] = diferenca_datas_dias(data_hora_hoje, dados['timestamp_added'])

	# parâmetros para a coleta de dados
	endereco = dados['address']
	params = {'max_time': data_hora_hoje, 'min_time': "2018-08-27T00:00:00Z"}

	# coleta de dados da primeira página
	resposta = requests.get('https://api.helium.io/v1/hotspots/%s/rewards' % endereco, params)
	recompensas = resposta.json()['data']
	try: cursor = resposta.json()['cursor']; mais_paginas = True
	except KeyError: mais_paginas = False

	# coleta das demais páginas (se houver)
	while mais_paginas:

		# coleta da página em questão a partir do cursor da anterior
		resposta = requests.get('https://api.helium.io/v1/hotspots?cursor=' + cursor)
		dados_resposta = resposta.json()

		# adição dos dados da página à lista completa
		try: recompensas += dados_resposta['data']
		except KeyError: pass

		# cláusula de finalização do loop
		try: cursor = dados_resposta['cursor']
		except KeyError: break

	# adição das recompensas ao dicionário do hotspot
	dados['rewards'] = recompensas

	# adição do dicionário do hotspot à lista geral
	dados_brutos.append(dados)

	# armazenamento de dados preventivo
	if indice % 50 == 0:
	    with open('dados/dados_brutos_incompletos_%s.json' % data_hoje, 'w') as file:
	        json.dump({'data': dados_brutos, 'date': data_hoje}, file)

	indice += 1

# armazenamento final dos dados em questão
with open('dados/dados_brutos_incompletos_%s.json' % data_hoje, 'w') as file:
	json.dump({'data': dados_brutos, 'date': data_hoje}, file)

# remove os dados incompletos dos hotspots
os.system('rm dados/todos_hotspots_%s.json' % data_hoje)

'''
PASSO 2 finalizado, daqui dai:
	- dados_brutos -> lista de dicionários, cada dict representa um hotspot
'''

# -- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- 2'

# PASSO 3: Coleta dos dados da quantidade de hotspots proximos a cada hotspot relevante  --- --- --- --- --- --- --- 3

# print de verbose
print('\nColetando dados de quantidade de hotspots próximos...')

# loop de coleta
indice = 0
for hotspot in tqdm(todos_hotspots):

	# renome das informações relevantes
	longitude = hotspot['lng']
	latitude = hotspot['lat']

	# verificação das informações relevantes
	try: longitude = float(hotspot['lng']); latitude = float(hotspot['lat'])
	except:
		hotspot['nearby hotspots'] = np.nan
		dados_brutos[indice].update(hotspot)
		continue

	# determinação dos parâmetros de solicitação
	params = {'lat': latitude, 'lon': longitude, 'distance': 2000}

	# solicitação
	resposta = requests.get('https://api.helium.io/v1/hotspots/location/distance', params)

	# bandeira de páginas extras
	mais_paginas = False

	# caso resposta válida
	if str(resposta) == '<Response [200]>':
		dados_resposta = resposta.json()['data']
		try: cursor = resposta.json()['cursor']; mais_paginas = True
		except KeyError: mais_paginas = False
		hotspot['nearby hotspots'] = len(dados_resposta)

	# caso mais páginas
	while mais_paginas:

		# solicitação
		resposta = requests.get('https://api.helium.io/v1/hotspots/location/distance?cursor=%s' % cursor, params)

		# caso resposta válida
		if str(resposta) == '<Response [200]>':
			dados_resposta = resposta.json()['data']
			try: cursor = resposta.json()['cursor']; mais_paginas = True
			except KeyError: mais_paginas = False
			hotspot['nearby hotspots'] += len(dados_resposta)

	dados_brutos[indice].update(hotspot)

	# armazentamento de segurança
	if indice % 50 == 0:
		with open('dados_brutos_incompletos_%s.json' % data_hoje, 'w') as file:
			json.dump({'dados': dados_brutos}, file)

	indice += 1

# armazenamento final
os.system('rm todos_hotspots_%s.json' % data_hoje)
os.system('rm dados_brutos_incompletos_%s.json' % data_hoje)
with open('dados_brutos_%s.json' % data_hoje, 'w') as file:
    json.dump({'data': dados_brutos, 'date': data_hoje}, file)

'''
PASSO 3 finalizado, daqui sai:
	- dados_brutos -> lista de dicionários
'''

# -- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- 3'






