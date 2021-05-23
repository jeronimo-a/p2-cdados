''' Script de coleta de dados da API do Helium Network '''

from tqdm import tqdm
from funcoes import *

import json
import requests
import pandas as pd
import datetime as dt


data_hoje = str(dt.date.today())
data_hoje = "%sT00:00:00Z" % data_hoje


# --  Coleta dos dados sobre os hotspots existentes	 --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---

print('Coletando dados sobre os hotspots existentes...\n')
print('\t0')

resposta = requests.get('https://api.helium.io/v1/hotspots')
dados = resposta.json()
cursor = dados['cursor']
hotspots = dados['data']

print('\t' + str(len(hotspots)))

while True:

    resposta = requests.get('https://api.helium.io/v1/hotspots?cursor=' + cursor)

    dados = resposta.json()
    hotspots += dados['data']

    print('\t' + str(len(hotspots)))

    try: cursor = dados['cursor']
    except KeyError: break

# -- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---


# armazenamento dos dados brutos sobre os hotspots
dados_brutos = {'dados': hotspots}
with open('dados_brutos.json', 'w') as json_file:
	json.dump(dados_brutos, json_file)


# --  Filtragem dos hotspots "inativos"	 --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---

bloco_atual = requests.get('https://api.helium.io/v1/blocks/height').json()['data']['height']

tolerancia = 24		# tolerância de atraso (número de blocos faltando)

hotspots_relevantes = list()

for hotspot in hotspots:
    altura = hotspot['status']['height']
    if altura != None:
        if altura >= bloco_atual - tolerancia: hotspots_relevantes.append(hotspot)

# -- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---


# -- Coleta dos dados de rendimento dos hotspots relevantes  --- --- --- --- --- --- --- --- --- --- --- --- ---

print('\nColetando dados de rendimento dos hotspots relevantes...')

hotspots_dados = list()

indice = 0
for hotspot in tqdm(hotspots_relevantes):
    
    dados = dict()
    dados['nome'] = hotspot['name']
    dados['data de adicao'] = hotspot['timestamp_added']
    dados['endereco'] = hotspot['address']
    dados['altura'] = hotspot['status']['height']
    dados['idade'] = diferenca_datas_dias(data_hoje, dados['data de adicao'])
    
    endereco = dados['endereco']
    params = {'max_time': data_hoje, 'min_time': "2018-08-27T00:00:00Z"}
    dados_retorno = requests.get('https://api.helium.io/v1/hotspots/:%s/rewards/sum' % endereco, params)
    dados_retorno = dados_retorno.json()['data']
    
    dados.update(dados_retorno)
    
    hotspots_dados.append(dados)
    
    if indice % 50 == 0:
        with open('hotspots_dados.json', 'w') as file:
            json.dump({'dados': hotspots_dados}, file)
    
    indice += 1

# -- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---

# armazenamento final dos dados
hotspots_dataframe = pd.DataFrame(hotspots_dados)
writer = pd.ExcelWriter('hotspots_dados.xlsx')
hotspots_dataframe.to_excel(writer)
writer.save()










