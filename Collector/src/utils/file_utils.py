class ImagePathProcessor:
    @staticmethod
    def get_image_name(image_path):
        # Separar o caminho pelos delimitadores "/"
        path_parts = image_path.split('/')
        # Pegar o último elemento da lista, que é o nome da imagem com extensão
        image_name = path_parts[-1]
        return image_name
