from pypylon import pylon
import json
import time

# Connect to the first camera found
camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())

# Open the camera
camera.Open()

# Enable auto exposure
camera.ExposureAuto.SetValue('Continuous')

# Enable auto gain
camera.GainAuto.SetValue('Continuous')

# Enable auto white balance if available
node_map = camera.GetNodeMap()
if node_map.GetNode("BalanceWhiteAuto"):
    camera.BalanceWhiteAuto.SetValue('Continuous')

# Wait for a few seconds to let the automatic adjustments take effect
time.sleep(2)

# Disable automatic adjustments to save the final values
camera.ExposureAuto.SetValue('Off')
camera.GainAuto.SetValue('Off')
if node_map.GetNode("BalanceWhiteAuto"):
    camera.BalanceWhiteAuto.SetValue('Off')

# Get the adjusted values
exposure_time = camera.ExposureTime.GetValue()
gain = camera.Gain.GetValue()
balance_ratio = camera.BalanceRatio.GetValue() if node_map.GetNode("BalanceRatio") else None

# Create a dictionary with the configurations
configurations = {
    'ExposureTime': exposure_time,
    'Gain': gain,
    'BalanceRatio': balance_ratio
}

# Save the configurations to a JSON file
with open('camera_configurations.json', 'w') as config_file:
    json.dump(configurations, config_file, indent=4)

# Close the camera
camera.Close()

print("Configurations saved in 'camera_configurations.json'.")
