import time
from src.gpio_com.gpio_class import GPIOReader

def main():
    # Define the GPIO pins to monitor
    gpio_pins = [300, 301, 302]
    
    # Initialize the GPIO reader for the defined pins
    gpio_reader = GPIOReader(gpio_pins)
    
    try:
        print("Starting GPIO monitor...")
        
        # Continuously check for falling edges
        while True:
            gpio_reader.detect_falling_edges()  # Detect falling edges on the GPIO pins
            
            # Optionally, print the current falling edge counts for all pins
            edge_counts = gpio_reader.get_edge_count()
            print(f"Falling edge counts: {edge_counts}")
            
            # Sleep for a short time to avoid overwhelming the system with too many reads
            time.sleep(0.05)
    
    except KeyboardInterrupt:
        print("GPIO monitoring stopped by user.")

if __name__ == "__main__":
    main()
