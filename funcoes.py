''' Módulo de funções do projeto '''

def diferenca_datas_dias(data_inicial, data_final):

	data_inicial = data_inicial[:10].split('-')
	data_final = data_final[:10].split('-')

	ano_inicial = int(data_inicial[0])
	mes_inicial = int(data_inicial[1])
	dia_inicial = int(data_inicial[2])

	data_inicial = ano_inicial * 365.25 + mes_inicial * 365.25 / 12 + dia_inicial

	ano_final = int(data_final[0])
	mes_final = int(data_final[1])
	dia_final = int(data_final[2])

	data_final = ano_final * 365.25 + mes_final * 365.25 / 12 + dia_final

	return data_inicial - data_final



