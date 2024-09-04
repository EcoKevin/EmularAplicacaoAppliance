import os

def export_gpio(gpio_num):
    try:
        # Export the GPIO pin
        with open('/sys/class/gpio/export', 'w') as f:
            f.write(str(gpio_num))
        print(f"GPIO {gpio_num} exported successfully.")
    except IOError:
        print(f"GPIO {gpio_num} is already exported.")

def set_gpio_direction(gpio_num, direction):
    try:
        direction_path = f'/sys/class/gpio/gpio{gpio_num}/direction'
        with open(direction_path, 'w') as f:
            f.write(direction)
        print(f"GPIO {gpio_num} set to {direction}.")
    except IOError as e:
        print(f"Error setting GPIO {gpio_num} direction: {e}")

def setup_gpios():
    gpio_nums = input("Enter the GPIO numbers you want to export (comma-separated): ")
    gpio_nums = [int(num.strip()) for num in gpio_nums.split(",")]

    for gpio in gpio_nums:
        export_gpio(gpio)
        
        direction = input(f"Set direction for GPIO {gpio} (in/out): ").strip().lower()
        while direction not in ['in', 'out']:
            print("Invalid direction! Please enter 'in' or 'out'.")
            direction = input(f"Set direction for GPIO {gpio} (in/out): ").strip().lower()
        
        set_gpio_direction(gpio, direction)

if __name__ == "__main__":
    setup_gpios()
