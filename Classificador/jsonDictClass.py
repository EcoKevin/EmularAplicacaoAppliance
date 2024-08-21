import json

class ClassificationDict:
    def __init__(self):
        self.data = {
            "id": None,
            "nome_imagem": None,
            "banda_id":None,
            "nr_sequencial":None,
            "linha_id":None,
            #"created_at":None,
            "tipo_ia":None,
            "industria_id":None,
            "dt_abate":None,
            "regions": []
        }
        self.add_region('carcaca')
    def insert_extra_info(self,info):
        self.data['id']=info[0]
        self.data['nome_imagem']=info[1]
        self.data['banda_id']=info[2]
        self.data['nr_sequencial']=info[3]
        self.data['linha_id']=info[4]
        self.data['created_at']=info[5].strftime("%Y-%m-%d %H:%M:%S")
        self.data['tipo_ia']=info[6]
        self.data['industria_id']=info[7]
        self.data['dt_abate']=info[8].strftime("%Y-%m-%d")
    def add_region(self, region_name):
        region = {
            "region_name": region_name,
            "defect_count": {},
            "defects": []
        }
        self.data["regions"].append(region)
    def get_defect_index(self,defect_names_with_indexes,defect_name):
        for index, tup in enumerate(defect_names_with_indexes):
            if tup[1] == defect_name:
                return index
        return -1


    def add_defect(self, region_index, defect_name, confidences, coordinates):
        defect_list=self.data['regions'][0]['defects']
        #Gets all registered defects and their indexes
        defect_names_with_indexes = [(index, defect['defect_name']) for index, defect in enumerate(defect_list)]
        #Check is the current defect is already on the info_dict
        is_new_defect_present=any(defect_name == defect_in_tuple for _, defect_in_tuple in defect_names_with_indexes)
        #If there is already the same defect, just appends new results
        if is_new_defect_present:
            defect_index=self.get_defect_index(defect_names_with_indexes,defect_name)
            self.data["regions"][region_index]["defects"][defect_index]['confidence'].append(confidences)
            self.data["regions"][region_index]["defects"][defect_index]['coordinates'].append(coordinates)
            self.data["regions"][region_index]["defects"][defect_index]['occurance_count']+=1
           # print(self.data["regions"][region_index]["defect_count"])
            self.data["regions"][region_index]["defect_count"][defect_name]+=1
            pass
        #If not, inserts new entry for defect list
        else:
            defect = {
                "defect_name": defect_name,
                "occurance_count": 1,
                "confidence": [confidences],
                "coordinates": [coordinates]
            }
            self.data["regions"][region_index]["defects"].append(defect)
            self.data["regions"][region_index]["defect_count"][defect_name]=1

    def insert_all_results(self,all_results):
        for defects in all_results:
            self.add_defect(0,defects['class_name'],defects['confidence'],defects['xyxy'])
    def generate_classification_json(self):
        return json.dumps(self.data)
    def get_data(self):
        return self.data