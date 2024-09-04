import threading
from pypylon import pylon
import time
import cv2
import os
from datetime import datetime
import numpy as np
from ultralytics import YOLO
from copy import deepcopy
from src.controller.image_controller import ImageController
from src.utils.file_utils import ImagePathProcessor
from src.gpio_com.gpio_class import GPIOReader
import re
import subprocess
import errno
from concurrent.futures import ThreadPoolExecutor
import logging
import queue  # Import queue module for FIFO

class CameraController:
    def __init__(self):
        # Constants and Configurations
        self.GRAB_TIMEOUT_MS = 5000
        self.EXPOSURE_TIME = 4000
        self.OUTPUT_PATH = "./SavedImages"
        self.OUTPUT_PATH_FULL = "./SavedImages"
        self.BRIGHTNESS_FACTOR = 2
        self.EXPOSURE_FACTOR = 2
        self.image_name = None
        self.image_path = None


        # Initialize camera and converter
        self.camera, self.converter = self.initialize_camera()
        self.configure_camera()

        # Initialize image controller
        self.image_controller = ImageController()
        self.image_path_processor = ImagePathProcessor()

        # Initialize the FIFO queue
        self.image_queue = queue.Queue()
        
        
        #Initializes DIReader
        self.DIReader=GPIOReader([300, 301,302,303])
        
        # Start the image-saving thread
        self.executor = ThreadPoolExecutor(max_workers=3)
        # Start Counters
        self.count_photos=0

        # Start capturing images
        #self.capture_images()
        self.executor.submit(self.continuous_DI_reading, self.DIReader)
        self.executor.submit(self.save_images_from_queue)
        self.executor.submit(self.capture_images())

        
        

    def initialize_camera(self):
        """Initialize and start grabbing frames from the camera."""
        camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
        camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
        converter = pylon.ImageFormatConverter()
        converter.OutputPixelFormat = pylon.PixelType_BGR8packed
        converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
        return camera, converter

    def configure_camera(self):
        """Configure camera settings."""
        
        #desired_frame_rate = 30  # Change this to your desired frame rate
        #self.camera.AcquisitionFrameRateEnable.SetValue(True)
        #self.camera.AcquisitionFrameRateAbs.Value = desired_frame_rate
        
        #self.camera.BalanceWhiteAuto.SetValue("Continuous")
        #self.camera.GainAuto.SetValue("Continuous")
        #self.camera.ExposureAuto.SetValue('Continuous')
        # self.camera.ExposureTimeRaw.SetValue(self.EXPOSURE_TIME)

    def save_image(self, img):
        """Save the adjusted image with a timestamped filename."""
        start_time = time.time()

        # Get image path and name
        self.image_path = self.image_controller.get_image_name(1, 1, 1)
        # -----------------------
        
        if not self.image_path:
            logging.error("Failed to retrieve image path from database.")
            return

        get_name_time = time.time()
        logging.debug(f'Time to get image name query: {get_name_time - start_time:.6f} seconds')
        logging.warning(f'Time to get image name query: {get_name_time - start_time:.6f} seconds')
        if get_name_time - start_time>0.2:
          logging.debug(f'Name consultation took a long time')
          
          
        #Gets image name from path obtained from DB  
        self.image_name = self.image_path_processor.get_image_name(self.image_path)
        #  --------------------
        
        
        # Construct the full file path
        file_name = os.path.join(self.OUTPUT_PATH, self.image_name)
        
        # Save the image to disk
        cv2.imwrite(file_name, img)
        
        write_time = time.time()
        logging.debug(f'Time to save image file in DISK : {write_time - get_name_time:.6f} seconds')
        logging.warning(f'Time to save image file in DISK : {write_time - get_name_time:.6f} seconds')
        total_time = write_time - start_time
        logging.debug(f'Total time to save image: {total_time:.6f} seconds')

    def save_image_full(self, img):
        file_name = os.path.join(self.OUTPUT_PATH_FULL, f"frame_{self.image_name}")
        cv2.imwrite(file_name, img)

    def process_and_save_image(self, img_adjusted):
        logging.debug('Captured image')
        starting_time = time.time()
        ## Gets image name from DB and saves image on disk
        self.save_image(img_adjusted)
        # ----------------------
        
        save_time = time.time()
        logging.debug(f'Total Time to save {save_time - starting_time}')
        logging.warning(f'Total Time to save {save_time - starting_time}')
        
        
        ## Updates image status on DB so it can be classified
        self.image_controller.update_image_status(1)
        # ---------------------
        
        
        db_time = time.time()
        logging.debug(f'Time to UPDATE STATUS {db_time - save_time}')
        logging.warning(f'Time to UPDATE STATUS {db_time - save_time}')

    def continuous_DI_reading(self, DIReader):
        while self.camera.IsGrabbing():
            ## Timer to prevent bounce effect
            time.sleep(0.01)
            
            ## Counts number of falling edges
            DIReader.detect_falling_edges()
            
    def save_images_from_queue(self):
        """Continuously save images from the FIFO queue."""
        
        while True:
            
            time.sleep(0.005)
            logging.debug(f'<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<Queue Size: {self.image_queue.qsize()}')
            try:
                logging.debug(f'<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<Queue Size: {self.image_queue.qsize()}')
                a=time.time()
                
                ## Retrieves image from  FIFO
                img_adjusted = self.image_queue.get(timeout=0.1)  # Waits up to 0.1 second for an item
                # ---------------------
                
                ## Processes imagem including getting image name, saving on disk and updating status to DB
                self.process_and_save_image(img_adjusted)
                # ---------------------
                
                
                self.image_queue.task_done()
                logging.debug(f'-------------------------------------------------- Time to processe queue item: {time.time()-a}')
            except queue.Empty:
                continue  # If the queue is empty, keep checking
                
        
    def snapshot_check(self,DIReader,grab_result,photo_taken_flag):
          capture_snapshot=False
          img_adjusted=None
          #Checks first DI status 
          if not DIReader.gpio_get_value(300):
               # If True, then check the second one
               if not DIReader.gpio_get_value(301) and photo_taken_flag:
               
                 init=time.time()
                 capture_snapshot = True # Sets photo_taken_flag to True so that this image is added to FIFO
                 #Gets image from camera
                 image = self.converter.Convert(grab_result)
                 # ---------------------
                 
                 
                 convert_time=time.time()
                 logging.debug(f'Convert time of {convert_time-init}')
                 if convert_time-init>0.2:
                   logging.debug(f'Convert took a LOOOOOOOOOOOOOOOOOONG time of {convert_time-init}')
                 logging.warning(f'Convert time of {convert_time-init}')
                 
                 
                 ##Converts to array and rotates image
                 img = image.GetArray()
                 img_adjusted = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
                 # ---------------------
                 
                 get_array_rotate_time=time.time()
                 logging.debug(f'get array and rotate  time of {get_array_rotate_time-convert_time}')
                 logging.warning(f'get array and rotate  time of {get_array_rotate_time-convert_time}')
                 self.count_photos += 1
                 logging.debug(f'Total images captured: {self.count_photos}')
                 logging.warning(f'Total images captured: {self.count_photos}')
                 
                 #Flag to prevent taking multiple instances of the same photo
                 photo_taken_flag=0
           
          else:
               
               logging.debug('Skipped capturing image')
               logging.debug(f'Reset photo_taken_flag')
               
               
               # Resets flag so different photo can be taken
               photo_taken_flag=1
               
               
          return capture_snapshot,img_adjusted,photo_taken_flag

    def capture_images(self):
        ## Main loop
        
        # Saves current camera configs
        try:
            pylon.FeaturePersistence.Save('basler_config_Kevin.data', self.camera.GetNodeMap())
            print('Configurations saved to basler_config_Kevin.data')
        except Exception as e:
            print(e)
            
            
        print('Starting Camera')
        time.sleep(4)
        print('Good to Go')
        
        
        #Initialize counters, timers and create output folder   
        os.makedirs(self.OUTPUT_PATH, exist_ok=True)
        count_fps = 0
        count_photos = 0
        count_queue=0
        count_grab=0
        count_iterations=0
        count_process=0
        DI0=-1
        DI1=-1
        photo_taken_flag=1
        fps_t = time.time()
  
        #Initialize GPIO Reader
        #DIReader = GPIOReader([300, 301])
        DI0_old,DI1_old,_,_=self.DIReader.get_edge_count()
        logging.basicConfig(level=logging.DEBUG, filename='debug.log', filemode='w')
        
        
        # Start DI reading and queue processing in separate threads
        #self.executor.submit(self.continuous_DI_reading, self.DIReader)
        #self.executor.submit(self.save_images_from_queue)
        
        
        
        while self.camera.IsGrabbing():
            # Start Timers and try to retrieve camera reading
            capture_snapshot = False            
            start_time = time.time()
            grab_time = time.time()
            
            ## Retrieves camera result
            grab_result = self.camera.RetrieveResult(self.GRAB_TIMEOUT_MS, pylon.TimeoutHandling_ThrowException)
            # --------------------------
            
            
            count_fps += 1
            logging.debug(f'Time to grab image: {grab_time - start_time:.4f} seconds')
            
            if grab_result.GrabSucceeded():
                count_iterations+=1

                # Logs if took more than 50 ms
                if grab_time - start_time>0.05:
                  count_grab+=1
                  logging.debug(f'####################################################### Time to Grab {grab_time - start_time:.4f} ##############################')
                  logging.debug(f'####################################################### Total times this happenened so far {count_grab} of {count_iterations}##############################')  
                # Updates current edge counts
                  
                DI0,DI1,a,b=self.DIReader.get_edge_count()  

                logging.debug(f'Sensors: DI0={DI0}, DI1={DI1}, old values : {DI0_old},{DI1_old}')
                

            
                
                
                ## Returns if capture conditions were met and the img captured
                capture_snapshot,img_adjusted,photo_taken_flag=self.snapshot_check(self.DIReader,grab_result,photo_taken_flag)
                # ----------------------------
                
                
                processing_time = time.time()
                logging.debug(f'Time to process image: {processing_time - grab_time:.4f} seconds')
                if (processing_time - grab_time)>0.2:
                  count_process+=1
                  print(f'Total loss due processing time: {count_process}')
                  logging.debug(f'Time to process image: {processing_time - grab_time:.4f} seconds VEEEEEEEEEEEEEEEEEEEEEEEEERY LOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOONG')
                
                
                
                if capture_snapshot:
                    # Add the image to the queue
                    count_queue+=1
                    logging.debug(f'-----------------------------------------------------------Total images added to queue: {count_queue}')
                    logging.debug(f'<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<Queue Size: {self.image_queue.qsize()}')
                    print('<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<Queue Size: ',self.image_queue.qsize())
                    before_q=time.time()
                    self.image_queue.put(img_adjusted)
                

                print(f'Total edge counts: {DI0},{DI1},{a},{b} and total photos taken: {count_queue}')
                if time.time() - fps_t > 1:
                    logging.debug(f'^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ FPS: {count_fps} ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^')
                    count_fps = 0
                    fps_t = time.time()
            else:
              #In case no results were retrieved from camera
              logging.debug('Erro 91')    
              
            grab_result.Release()
            DI0_old = DI0
            DI1_old = DI1

        self.camera.StopGrabbing()
        cv2.destroyAllWindows()


