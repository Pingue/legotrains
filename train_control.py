#!/usr/bin/env python3
"""
Simple LEGO Train Control Script
Controls a LEGO train to go forward for 5 seconds, then reverse for 5 seconds.
Uses bleak library directly - works with stock LEGO firmware (no flashing required).
"""

import asyncio
import time
from bleak import BleakScanner, BleakClient

# LEGO Powered Up characteristic UUID for sending commands
LEGO_CHARACTERISTIC_UUID = "00001624-1212-efde-1623-785feabcd123"

# Speed as percentage (-100 to 100)
FORWARD_SPEED = 50
REVERSE_SPEED = -50
PORT = 0x00  # Port A (0x00), Port B is 0x01

def create_motor_command(port, speed):
    """Create a motor control command for LEGO Powered Up."""
    # Convert speed percentage to motor value (-100 to 100)
    speed_value = max(-100, min(100, int(speed)))
    if speed_value < 0:
        speed_byte = 256 + speed_value  # Convert to unsigned byte
    else:
        speed_byte = speed_value
    
    # Working command format discovered from testing:
    # [length, hub_id, message_type, port, mode, startup_completion, power, max_power, use_profile]
    # 0x11 = write direct mode data
    # 0x01 = execute immediately with command feedback
    return bytes([0x08, 0x00, 0x81, port, 0x11, 0x01, speed_byte, 0x64, 0x7f])

async def control_train():
    """Main async function to control the train."""
    try:
        # Scan for LEGO Powered Up devices
        print("Scanning for LEGO Powered Up hub via Bluetooth...")
        print("(Make sure your train hub is powered on)")
        
        devices = await BleakScanner.discover(timeout=10.0)
        
        lego_device = None
        
        # Try to find LEGO device by name
        for device in devices:
            if device.name and any(keyword in device.name.upper() for keyword in ["TRAIN", "HUB", "MOVE", "CITY", "LEGO"]):
                lego_device = device
                print(f"Found LEGO device: {device.name}")
                break
        
        if not lego_device:
            print("✗ No LEGO Powered Up hub found!")
            return 1
        
        print(f"✓ Connecting to {lego_device.name}...")
        
        async with BleakClient(lego_device.address) as client:
            print("✓ Connected to hub successfully!")
            
            print("\nStarting train control sequence...")
            
            # Go forward for 5 seconds
            print(f"→ Going forward at speed {FORWARD_SPEED}%")
            command = create_motor_command(PORT, FORWARD_SPEED)
            await client.write_gatt_char(LEGO_CHARACTERISTIC_UUID, command)
            await asyncio.sleep(5)
            
            # Go reverse for 5 seconds
            print(f"← Going reverse at speed {REVERSE_SPEED}%")
            command = create_motor_command(PORT, REVERSE_SPEED)
            await client.write_gatt_char(LEGO_CHARACTERISTIC_UUID, command)
            await asyncio.sleep(5)
            
            # Stop the motor
            print("■ Stopping train...")
            command = create_motor_command(PORT, 0)
            await client.write_gatt_char(LEGO_CHARACTERISTIC_UUID, command)
            
            print("\n✓ Train control complete!")
        
        return 0
        
    except Exception as e:
        print(f"✗ Error: {type(e).__name__}: {e}")
        print(f"  Check that:")
        print(f"  - Hub is powered on and in range")
        print(f"  - Bluetooth is enabled on your computer")
        return 1

def main():
    """Main entry point."""
    return asyncio.run(control_train())

if __name__ == "__main__":
    exit(main())
