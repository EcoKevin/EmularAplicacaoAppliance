import os
import time
import threading

class Temporizer:
    def __init__(self, duration_ms,name='Default'):
        self.duration = duration_ms / 1000.0  # Convert to seconds
        self.start_time = None
        self.name=name


    def start_timer(self):
        #print('Started Timer')
        self.start_time = time.time()

    def reset_timer(self):
        self.start_time = None


    def is_running(self):
        if self.start_time is None:
            return False
        return (time.time() - self.start_time) < self.duration

    def check_and_reset(self):
        if self.start_time is None:
            #print('Is None')
            return False
        if (time.time() - self.start_time) >= self.duration:
            #print('Time Overflow')
            self.reset_timer()
            return False
        return True


class GPIOReader:
    SUCCESS = 0
    FAIL = -1

    def __init__(self, gpio_pins):
        self.gpio_pins = gpio_pins
        self.previous_values = {gpio: 0 for gpio in gpio_pins}  # Assume initial state is low (0)
        self.falling_edge_counts = {gpio: 0 for gpio in gpio_pins}
        self.DI_Temp={gpio: Temporizer(100,str(gpio)) for gpio in gpio_pins}

    def gpio_export(self, gpio):
        gpio_path = f"/sys/class/gpio/gpio{gpio}"
        if not os.path.exists(gpio_path):
            try:
                with open("/sys/class/gpio/export", "w") as f:
                    f.write(f"{gpio}")
            except Exception as e:
                print(f"Error exporting GPIO {gpio}: {e}")
                return self.FAIL
        return self.SUCCESS

    def gpio_set_direction(self, gpio, direction):
        gpio_path=f'/sys/class/gpio/gpio{gpio}/direction'
        if not os.path.exists(gpio_path):
          try:
              with open(f"/sys/class/gpio/gpio{gpio}/direction", "w") as f:
                  f.write(direction)
          except Exception as e:
              print(f"Error setting direction for GPIO {gpio}: {e}")
              return self.FAIL
        return self.SUCCESS

    def gpio_get_value(self, gpio):
        try:
            with open(f"/sys/class/gpio/gpio{gpio}/value", "r") as f:
                value = f.read().strip()
                return int(value)
        except Exception as e:
            print(f"Error reading value from GPIO {gpio}: {e}")
            return self.FAIL

    def read_di_channel(self, gpio):
        if self.gpio_export(gpio) == self.FAIL:
            print(f'Failed to export GPIO {gpio}')
            return self.FAIL
        
        if self.gpio_set_direction(gpio, "in") == self.FAIL:
            print(f'Failed to set direction for GPIO {gpio}')
            return self.FAIL
        
        value = self.gpio_get_value(gpio)
        if value == self.FAIL:
            print(f'Failed to read value from GPIO {gpio}')
            return self.FAIL
        
        return value
    def get_edge_count(self):
      return [value for value in  self.falling_edge_counts.values()]
       
    def detect_falling_edges(self):
        for gpio in self.gpio_pins:
            current_value = self.read_di_channel(gpio)
            
            if current_value != self.FAIL:
                self.DI_Temp[gpio].check_and_reset()
                if self.previous_values[gpio] == 1 and current_value == 0:
                    self.falling_edge_counts[gpio] += 1
                    self.DI_Temp[gpio].start_timer()
                    '''
                    if self.DI_Temp[gpio].check_and_reset():
                      
                      pass
                    else:
                      
                      self.DI_Temp[gpio].start_timer()
                    #self.DI_Temp[gpio].start_timer()
                    '''
                    #print(f"Falling edge detected on DI channel {gpio - 300}. Current count: {self.falling_edge_counts[gpio]}")
                self.previous_values[gpio] = current_value