#!/usr/bin/env python3
"""
LEGO Train Control Web App
A kid-friendly Flask web interface for controlling a LEGO train.
"""

import asyncio
import threading
from flask import Flask, render_template, jsonify, request
from bleak import BleakScanner, BleakClient

app = Flask(__name__)

# LEGO Powered Up configuration
LEGO_CHARACTERISTIC_UUID = "00001624-1212-efde-1623-785feabcd123"
PORT = 0x00  # Port A

# Global state - support for 2 trains
trains = {
    'train1': {'client': None, 'device': None, 'speed': 0, 'name': 'Train 1'},
    'train2': {'client': None, 'device': None, 'speed': 0, 'name': 'Train 2'}
}
background_loop = None
background_thread = None

def create_motor_command(port, speed):
    """Create a motor control command for LEGO Powered Up."""
    speed_value = max(-100, min(100, int(speed)))
    if speed_value < 0:
        speed_byte = 256 + speed_value
    else:
        speed_byte = speed_value
    
    return bytes([0x08, 0x00, 0x81, port, 0x11, 0x01, speed_byte, 0x64, 0x7f])

def start_background_loop():
    """Start a background event loop for async operations."""
    global background_loop
    background_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(background_loop)
    background_loop.run_forever()

def run_coroutine_threadsafe(coro):
    """Run a coroutine in the background event loop."""
    if background_loop is None:
        raise Exception("Background loop not started")
    future = asyncio.run_coroutine_threadsafe(coro, background_loop)
    return future.result(timeout=10)

async def find_trains():
    """Find all LEGO train hubs."""
    devices = await BleakScanner.discover(timeout=10.0)
    
    found_trains = []
    for device in devices:
        if device.name and any(keyword in device.name.upper() for keyword in ["TRAIN", "HUB", "MOVE", "CITY", "LEGO"]):
            found_trains.append(device)
    
    return found_trains

async def connect_to_train(train_id):
    """Connect to a specific LEGO train hub."""
    global trains
    
    train = trains[train_id]
    
    # If already connected, return True
    if train['client'] and train['client'].is_connected:
        return True
    
    # Find all available trains
    found_trains = await find_trains()
    
    if not found_trains:
        return False
    
    # Try to assign trains based on what's available
    # If this train doesn't have a device yet, assign the next available one
    if train['device'] is None:
        # Find a device that's not already assigned to another train
        assigned_devices = [trains[tid]['device'] for tid in trains if trains[tid]['device'] is not None]
        for device in found_trains:
            if device not in assigned_devices:
                train['device'] = device
                train['name'] = device.name
                break
    
    if train['device'] is None:
        return False
    
    # Connect to the device
    train['client'] = BleakClient(train['device'].address)
    await train['client'].connect()
    return train['client'].is_connected

async def connect_all_trains():
    """Try to connect to all available trains."""
    found_trains = await find_trains()
    
    if not found_trains:
        return 0
    
    # Assign devices to train slots
    for i, device in enumerate(found_trains[:2]):  # Only take first 2
        train_id = f'train{i+1}'
        trains[train_id]['device'] = device
        trains[train_id]['name'] = device.name
        trains[train_id]['client'] = BleakClient(device.address)
        await trains[train_id]['client'].connect()
    
    return len([t for t in trains.values() if t['client'] and t['client'].is_connected])

async def set_train_speed(train_id, speed):
    """Set the train speed for a specific train."""
    global trains
    
    train = trains[train_id]
    
    if not train['client'] or not train['client'].is_connected:
        if not await connect_to_train(train_id):
            raise Exception(f"Not connected to {train_id}")
    
    command = create_motor_command(PORT, speed)
    await train['client'].write_gatt_char(LEGO_CHARACTERISTIC_UUID, command)
    train['speed'] = speed
    
    # Store last command for debug
    train['last_command'] = command.hex()

async def get_train_info(train_id):
    """Get detailed information about a train."""
    global trains
    
    train = trains[train_id]
    
    if not train['client'] or not train['client'].is_connected:
        return None
    
    info = {
        'name': train['name'],
        'speed': train['speed'],
        'connected': True,
        'address': train['device'].address if train['device'] else None,
        'last_command': train.get('last_command', 'None'),
    }
    
    # Try to read battery level
    try:
        # Request hub properties - battery voltage
        hub_info_request = bytes([0x05, 0x00, 0x01, 0x06, 0x02])
        await train['client'].write_gatt_char(LEGO_CHARACTERISTIC_UUID, hub_info_request)
        await asyncio.sleep(0.5)
        info['battery_request_sent'] = True
    except Exception as e:
        info['battery_error'] = str(e)
    
    return info

@app.route('/')
def index():
    """Render the main control page."""
    return render_template('index.html')

@app.route('/api/status', methods=['GET'])
def status():
    """Get the current status of all trains."""
    connected_count = sum(1 for t in trains.values() if t['client'] is not None and t['client'].is_connected)
    
    return jsonify({
        'status': 'success',
        'connected_count': connected_count,
        'trains': {
            train_id: {
                'connected': train['client'] is not None and train['client'].is_connected,
                'speed': train['speed'],
                'name': train['name']
            }
            for train_id, train in trains.items()
        }
    })

@app.route('/api/connect', methods=['POST'])
def connect():
    """Connect to all available trains."""
    try:
        count = run_coroutine_threadsafe(connect_all_trains())
        
        if count > 0:
            connected_names = [t['name'] for t in trains.values() if t['client'] and t['client'].is_connected]
            return jsonify({
                'status': 'success', 
                'message': f'Connected to {count} train(s)',
                'trains': connected_names,
                'count': count
            })
        else:
            return jsonify({'status': 'error', 'message': 'No trains found'}), 404
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/scan', methods=['POST'])
def scan_and_connect():
    """Scan for new trains and connect them."""
    try:
        async def scan_for_new():
            found_trains = await find_trains()
            
            # Find which trains are already connected
            assigned_devices = [trains[tid]['device'] for tid in trains if trains[tid]['device'] is not None]
            
            # Connect to any new trains
            new_count = 0
            for device in found_trains:
                if device not in assigned_devices:
                    # Find an empty train slot
                    for train_id in trains:
                        if trains[train_id]['device'] is None:
                            trains[train_id]['device'] = device
                            trains[train_id]['name'] = device.name
                            trains[train_id]['client'] = BleakClient(device.address)
                            await trains[train_id]['client'].connect()
                            new_count += 1
                            break
            
            return new_count
        
        new_count = run_coroutine_threadsafe(scan_for_new())
        total_connected = len([t for t in trains.values() if t['client'] and t['client'].is_connected])
        
        return jsonify({
            'status': 'success',
            'message': f'Found {new_count} new train(s)',
            'total_connected': total_connected
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/rename', methods=['POST'])
def rename_train():
    """Rename a train."""
    try:
        data = request.get_json()
        train_id = data.get('train_id')
        new_name = data.get('name', '').strip()
        
        if not train_id or train_id not in trains:
            return jsonify({'status': 'error', 'message': 'Invalid train ID'}), 400
        
        if not new_name:
            return jsonify({'status': 'error', 'message': 'Name cannot be empty'}), 400
        
        trains[train_id]['name'] = new_name
        
        return jsonify({
            'status': 'success',
            'train_id': train_id,
            'name': new_name
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/speed', methods=['POST'])
def set_speed():
    """Set the train speed for a specific train."""
    try:
        data = request.get_json()
        train_id = data.get('train_id', 'train1')
        speed = int(data.get('speed', 0))
        
        run_coroutine_threadsafe(set_train_speed(train_id, speed))
        
        return jsonify({'status': 'success', 'train_id': train_id, 'speed': speed})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/speed/all', methods=['POST'])
def set_speed_all():
    """Set the same speed for all connected trains."""
    try:
        data = request.get_json()
        speed = int(data.get('speed', 0))
        
        async def set_all_speeds():
            for train_id in trains:
                if trains[train_id]['client'] and trains[train_id]['client'].is_connected:
                    await set_train_speed(train_id, speed)
        
        run_coroutine_threadsafe(set_all_speeds())
        
        return jsonify({'status': 'success', 'speed': speed})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/stop', methods=['POST'])
def stop():
    """Stop a specific train."""
    try:
        data = request.get_json()
        train_id = data.get('train_id', 'train1')
        
        run_coroutine_threadsafe(set_train_speed(train_id, 0))
        
        return jsonify({'status': 'success', 'train_id': train_id, 'speed': 0})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/stop/all', methods=['POST'])
def stop_all():
    ""

@app.route('/api/debug/<train_id>', methods=['GET'])
def get_debug_info(train_id):
    """Get debug information about a specific train."""
    try:
        if train_id not in trains:
            return jsonify({'status': 'error', 'message': 'Invalid train ID'}), 400
        
        info = run_coroutine_threadsafe(get_train_info(train_id))
        
        if info:
            return jsonify({'status': 'success', 'info': info})
        else:
            return jsonify({'status': 'error', 'message': 'Train not connected'}), 404
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    print("🚂 LEGO Train Control Web App")
    print("Starting background event loop...")
    
    # Start the background event loop in a separate thread
    background_thread = threading.Thread(target=start_background_loop, daemon=True)
    background_thread.start()
    
    # Give the loop time to start
    import time
    time.sleep(0.5)
    
    print("Open your browser to: http://localhost:5000")
    print("Make sure your train is powered on!")
    app.run(host='0.0.0.0', port=5000, debug=False)
