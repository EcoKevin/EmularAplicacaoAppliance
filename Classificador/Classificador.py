from DBHandlerClass import DBHandler
from jsonDictClass import ClassificationDict
from predictorClass import YOLOPredictor
import os
import random
import time
from datetime import datetime
import json


#model_path=r"C:\Users\Kevin\Documents\Kevin\PoutryTraceKevin\ResultadosServidor\8Indicadores\XLarge\weights\best.pt"
model_path="./models/4Classes/best.pt"

IMAGE_FOLDER='./Images'
#model_path=r"C:\Users\Kevin\Documents\Kevin\PoutryTraceKevin\ResultadosServidor\XLarge\weights\best.pt"
Model=YOLOPredictor(model_path)
DBH=DBHandler()

image_list=os.listdir(IMAGE_FOLDER)
previous_processed_results=[]
filtered_processed_results=[]

while True:
    #time.sleep(1)
    
    results=DBH.get_images_to_classify(40)
 
    
    if results:
        for item in results:
            random_number = random.randint(0, 423)
            classification_dict=ClassificationDict()

            image_db_path=item[1]
            image_name=image_db_path.split('/')[-1]
            image_name_no_frame=image_name.split('_')[-1]
            #print(image_name)
            image_path=os.path.join(IMAGE_FOLDER,image_list[random_number])
        
            image_id=item[0]
            data_abate=item[8]
            try:
                start_time=time.time()
                predicts=Model.predict(image_path)
                
                json_tempo=json.dumps({})
                
                processed_results,defect_list=Model.get_results_info(predicts)
                if processed_results:
                        filtered_processed_results=Model.filter_repeated_predictions(previous_processed_results,processed_results) 
                classification_dict.insert_all_results(processed_results)
                classification_dict.insert_extra_info(item[0:9])
                            # Save the dictionary as JSON
                classification_dict.data['id']=random_number
                
                json_clasificacao=classification_dict.generate_classification_json()
                status=2
                date=datetime.now()
                
                DBH.select_for_update(data_abate,defect_list)
                DBH.update_results_to_tb_imagem(status,date,json_tempo,json_clasificacao,image_id)
                current_time=time.time()
                print(f'Tempo para predição: {current_time-start_time} da imagem {image_name} using index {random_number}')
                #print(f'atualizou {image_id}')
                if filtered_processed_results:
                    previous_processed_results=filtered_processed_results
            except Exception as e:
                print(e)
                pass
    
    #print(f'\rTempo para processar {len(results)} imagens: {(current_time-start_time)} segundos       ',end="")




