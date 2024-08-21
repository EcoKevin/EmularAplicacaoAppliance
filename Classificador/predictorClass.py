## Obter dados de classificação
from ultralytics import YOLO
import cv2
import math 
import time
from copy import deepcopy
import os
import psycopg2



class YOLOPredictor:
    def __init__(self, model_path):
        self.model = self.load_model(model_path)
        #self.db_connection = self.setup_database(database_config)
        
    def load_model(self, model_path):
       return YOLO(model_path)


    def predict(self, image_path):
        project_name=r'D:\VisitaCVALE_Registros\23-04\Predicts'
        folder_name='4_Classes_Nano_StdAug_Full_Auto_1024_CVALE'
        # Perform prediction using the YOLO model
        predictions = self.model(image_path,imgsz=1024,device='cuda',save=True,verbose=False,project=project_name,name=folder_name,save_txt=True,exist_ok=True)
        return predictions
    def compare_y_coordinates(self,previous_results,current_results,threshold=10):
        similar_classes_idx=[]
        # Iterate over results in the first image
        for result1 in previous_results:
            class_name1 = result1['class_name']
            y1_min, y1_max = result1['xyxy'][1], result1['xyxy'][3]

            # Iterate over results in the second image
            for result2 in current_results:
                class_name2 = result2['class_name']
                y2_min, y2_max = result2['xyxy'][1], result2['xyxy'][3]
                
                # Check if the classes are the same and y-coordinates are similar
                if class_name1 == class_name2:
                    if abs(y1_min - y2_min) <= threshold or abs(y1_max - y2_max) <= threshold:
                        print(f"Class '{class_name1}' has similar y-coordinates in previou and current results")
                        print(f"Coordinates in previous results: {result1['xyxy']} index {previous_results.index(result1)}")
                        print(f"Coordinates in current results: {result2['xyxy']} index {current_results.index(result2)}")
                        print()
                        if current_results.index(result2) not in similar_classes_idx:
                            similar_classes_idx.append(current_results.index(result2))
        return similar_classes_idx
    def filter_repeated_predictions(self,previous_processed_results,processed_results):
        if previous_processed_results:
            similar_idx=self.compare_y_coordinates(previous_processed_results,processed_results)
            if similar_idx:
                print(similar_idx)
                similar_idx.sort()
                similar_idx.reverse()
                print(similar_idx)
                for idx in similar_idx:
                    print(f'Removing index {idx} with class {processed_results[idx]["class_name"]}')
                    processed_results.pop(idx)
        return processed_results
    def get_results_info(self,results):
        # Get class names from results[0].names
        class_names = results[0].names
        '''
        if len(class_names)>3:
            
            class_names={0:'Hematoma',1:'Ruptura',2:'Penugem',3:'Fratura',4:'Calo de Pata',5:'Falha Técnica',6:'Arranhadura',7:'Artrite'}
        '''
        class_names={0:'hematoma',1:'calo_de_pata',2:'fratura',3:'artrite'}
        # Initialize list to store results
        all_results = []
        found_labels=[]
        # Iterate through each prediction
        for i in range(len(results[0].boxes.cls)):
            # Get class ID, confidence, and xyxy coordinates
            class_id = results[0].boxes.cls[i].item()
            confidence = results[0].boxes.conf[i].item()
            xyxy = results[0].boxes.xyxy[i].tolist()

            # Get class name from class_names dict
            if class_id in class_names:
                class_name = class_names[class_id]
            else:
                class_name = "Unknown"
            if class_names[class_id]=='contaminacaofecal' or class_names[class_id]=='CF':
                name='contaminacao_fecal'
            elif class_names[class_id]=='contaminacaogastrica' or class_names[class_id]=='CG':
                name='contaminacao_gastrica'
            elif class_names[class_id]=='contaminacaobiliar' or class_names[class_id]=='CB':
                name='contaminacao_biliar'
            else:
                name=class_names[class_id]
            if name in found_labels:
                pass
            else:

                found_labels.append( name)
            # Create result dictionary
            result_info = {
                "class_id": class_id,
                "class_name": class_name,
                "confidence": confidence,
                "xyxy": xyxy
            }

            # Append result to list
            all_results.append(result_info)

        return all_results,found_labels
    def check_dupes(self,results,item_class):
        index_list=[]
        #Runs through the results, checking for instances of the desired item class
        for index,item in enumerate(results):
            class_name=item['class_name']
            #Saves it in a list
            if class_name.lower()==item_class:
                index_list.append(index)
        #If there is more than 1 on the list, it is possible to have a bilateral, so returns the results of that indexes
        if len(index_list)>1:
            return [results[i] for i in index_list]
        else:
        #If not, returns none.
            return None
    def find_centroid(self,dupe_results):

        centroid_list=[]
        for item in dupe_results:
            coordinates=item['xyxy']
            initial_x, initial_y = coordinates[0],coordinates[1]
            final_x, final_y = coordinates[2],coordinates[3]
            centroid_x = (initial_x + final_x) / 2
            centroid_y = (initial_y + final_y) / 2
            centroid=[centroid_x,centroid_y]
            centroid_list.append(centroid)


        return centroid_list
    def check_bilateral(self,results,item_class):
        x_offset_threshold=50
        dupe_results=self.check_dupes(results,item_class)
        if dupe_results == None:
            return None
        centroid_list=self.find_centroid(dupe_results)
        bi_list=[]
        for i,cent in enumerate(centroid_list):
            for j,cent2 in enumerate(centroid_list):
                x_i=cent[0]
                x_j=cent2[0]
                if abs(x_i-x_j)>x_offset_threshold:
                    bi_list.append((i,j))
        if bi_list:
            return bi_list
        else:
            return None
    
