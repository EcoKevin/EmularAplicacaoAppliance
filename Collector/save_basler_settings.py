import os
import dotenv

from pypylon import pylon

config_file_path = r'C:\Users\iureo\Documents\collector-aves\data\basler_config.data'
camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
camera.Open()

print("Usando Dispositivo: {}" .format(camera.GetDeviceInfo().GetModelName()))

try:
    pylon.FeaturePersistence.Save(config_file_path, camera.GetNodeMap())
    print("Arquivo de configurações da câmera salvo com sucesso!")
except pylon.RuntimeException as e:
    print("Erro ao salvar configurações da câmera:", e)
except Exception as ex:
    print("Erro desconhecido ao salvar configurações da câmera:", ex)

