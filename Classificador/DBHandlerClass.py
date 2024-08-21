from ultralytics import YOLO
import cv2
import math 
import time
from copy import deepcopy
import os
import psycopg2
from psycopg2 import sql
import json

class DBHandler:
    def __init__(self):
        self.conn = self.setup_database()

    def setup_database(self):
        # Replace placeholders with your actual credentials
        host = "localhost"
        port = 5432
        database = "db_industry_lar_ponto_1"  # Replace with your database name
        user = "db_industry_user"  # Replace with your Postgres username
        password = "db_industry_user"  # Replace with your Postgres password
        try:
            conn = psycopg2.connect(host=host, port=port, database=database, user=user, password=password)
            print("Connected to Postgres database!")
            return conn
        except (Exception, psycopg2.Error) as error:
            print("Error connecting to Postgres database:", error)
            exit()

    def get_images_to_classify(self, limit):
        with self.conn.cursor() as cursor:
            sql = sql = """
                            SELECT
                                id,
                                caminho_imagem,
                                aux_tb_banda_id,
                                nr_sequencial,
                                aux_tb_linha_id,
                                created_at,
                                aux_tb_tipo_ia_id,
                                industria_id,
                                tb_abate_data_abate,
                                aux_estado_imagem_id
                                
                            FROM
                                tb_imagem
                            WHERE
                                aux_estado_imagem_id = 1
                            ORDER BY
                                id DESC
                            LIMIT %s;
                        """
            cursor.execute(sql, (limit,))
            results = cursor.fetchall()
            return results

    def update_results_to_tb_imagem(self, status, time, json_tempo, json_classificacao, id):
        with self.conn.cursor() as cursor:
            query = """
                    UPDATE tb_imagem 
                    SET aux_estado_imagem_id = %s, 
                        dt_processamento = %s,
                        json_tempo_processamento = %s,
                        json_classificacao = %s 
                    WHERE id = %s
                    """
            cursor.execute(query, (status, time, json_tempo, json_classificacao, id))
            self.conn.commit()

    def update_data_json(self,data_json,lista_defeitos):
        #If data_json is not none, update it
        if data_json:
            if lista_defeitos:
                for defects in lista_defeitos:
                    if defects in data_json.keys():
                        data_json[defects]+=1
                    else:
                        data_json[defects]=1
            else:
                #There are no defects on the list
                #If there is already a healthy registry entry, increment it 
                if 'Saudavel' in data_json.keys():
                    data_json['Saudavel']+=1
                #If not, insert it
                else:
                    data_json['Saudavel']=1
                return json.dumps(data_json)
        #If no json, then we must create it 
        else:
            data_json={}
            if lista_defeitos:
                for defects in lista_defeitos:
                        data_json[defects]=1
            else:
                data_json['Saudavel']=1
        return json.dumps(data_json)
    def select_for_update(self, key_value,lista_defeitos):
        
            with self.conn:
                with self.conn.cursor() as cursor:
                    # Iniciar uma transação
                    cursor.execute("BEGIN;")
                    
                    # Executar SELECT FOR UPDATE
                    cursor.execute(sql.SQL("SELECT total_abatido, dados FROM tb_abate WHERE data_abate = %s FOR UPDATE;"), [key_value])
                    
                    # Aqui você pode manipular os dados bloqueados
                    results = cursor.fetchall()
                    total_atual=results[0][0]
                    total_novo=total_atual+1
                    json_atual=results[0][1]
                    dados_json=self.update_data_json(json_atual,lista_defeitos)
                    
                    
                    # Aqui você pode decidir se comete ou não a transação
                    # Se decidir não cometer, você pode usar conn.rollback() para reverter
                    # conn.commit() é chamado automaticamente ao sair do bloco 'with' se não houver erros
                    
                    # Manipulação opcional e commit
                    # Exemplo de atualização
                    cursor.execute(sql.SQL("UPDATE tb_abate SET total_abatido=%s, dados = %s WHERE data_abate = %s;"), [total_novo,dados_json, key_value])

# from ultralytics import YOLO
# import cv2
# import math 
# import time
# from copy import deepcopy
# import os
# import psycopg2

# class DBHandler:
#     def __init__(self):
#         self.conn=self.setup_database()
#     def setup_database(self):
#         # Replace placeholders with your actual credentials
#         host = "localhost"
#         port = 5432
#         database = "postgres"  # Replace with your database name
#         user = "postgres"  # Replace with your Postgres username
#         password = "16101992"  # Replace with your Postgres password
#         try:
#             conn = psycopg2.connect(host=host, port=port, database=database, user=user, password=password)
#             print("Connected to Postgres database!")
#             return conn
#         except (Exception, psycopg2.Error) as error:
#             print("Error connecting to Postgres database:", error)
#             exit()
#     def get_images_to_classify(self,limit):
#         with self.conn.cursor() as cursor:
#             sql = 'select id, nome_imagem,aux_estado_imagem_id from tb_imagem where aux_estado_imagem_id =1  order by id desc limit {};'.format(limit)
#             cursor.execute(sql)
#             results = cursor.fetchall()
#             #self.conn.close()
#             return results
#     def update_results_to_db(self,status,time,json_tempo,json_classificacao,id):
#         with self.conn.cursor() as cursor:
#             query = """UPDATE tb_imagem SET aux_estado_imagem_id = %s, dt_processamento = %s,json_tempo_processamento=%s, json_classificacao=%s WHERE id = %s"""
#             cursor.execute(query, (status, time,json_tempo,json_classificacao, id))  # Tuple with values to insert
#             self.conn.commit()
