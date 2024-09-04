import psycopg2
from dotenv import load_dotenv
import os
from psycopg2 import pool

class ImageController:
    _pool = None
    def __init__(self):
        load_dotenv()
        self.host = os.getenv("DB_HOST")
        self.database = os.getenv("DB_DATABASE")
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")
        self.connection = None
        self.connect()

    def connect(self):
        try:
            if ImageController._pool is None:
                ImageController._pool = psycopg2.pool.SimpleConnectionPool(
                    1, 20,  # minimum and maximum number of connections
                    host=self.host,
                    database=self.database,
                    user=self.user,
                    password=self.password
                )
            if ImageController._pool:
                print("Connection pool created successfully")
        except Exception as e:
            print("Error creating connection pool:", e)
    def get_connection(self):
        try:
            return ImageController._pool.getconn()
        except Exception as e:
            print("Error getting connection from pool:", e)
    def return_connection(self, conn):
        try:
            ImageController._pool.putconn(conn)
        except Exception as e:
            print("Error returning connection to pool:", e)
    def close_all_connections(self):
        try:
            ImageController._pool.closeall()
            print("All connections in the pool have been closed")
        except Exception as e:
            print("Error closing all connections in the pool:", e)
    def close_connection(self):
        if self.connection is not None:
            self.connection.close()
            print("Conexão fechada com o banco de dados PostgreSQL")

    def get_image_name(self, param1, param2, param3):
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            # Use a prepared statement to insert and retrieve the image path
            cursor.execute("""
                DO $$
                BEGIN
                    PERFORM func_inserir_imagem_frango(%s, %s, %s);
                END $$;
            """, (param1, param2, param3))
            conn.commit()

            cursor.execute("""
                SELECT caminho_imagem
                FROM tb_imagem
                ORDER BY created_at DESC
                LIMIT 1;
            """)
            result = cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            print("Error executing func_inserir_imagem_frango:", e)
        finally:
            if conn:
                self.return_connection(conn)
    def update_image_status(self, status):
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            # Use a prepared statement for updating the image status
            cursor.execute("""
                UPDATE tb_imagem
                SET aux_estado_imagem_id = %s
                WHERE created_at = (
                    SELECT created_at
                    FROM tb_imagem
                    ORDER BY created_at DESC
                    LIMIT 1
                );
            """, (status,))
            conn.commit()
        except Exception as e:
            print("Error updating image status:", e)
        finally:
            if conn:
                self.return_connection(conn)
