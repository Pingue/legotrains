# 🚂 LEGO Train Control Web App

A kid-friendly web interface for controlling LEGO Powered Up trains via Bluetooth. Control unlimited trains with an intuitive touchscreen-friendly interface.

![Multi Train Control](https://img.shields.io/badge/Trains-Unlimited-green) ![Python](https://img.shields.io/badge/Python-3.9+-blue) ![Platform](https://img.shields.io/badge/Platform-macOS-lightgrey)

## Features

✨ **Multi-Train Support** - Connect and control any number of LEGO Powered Up trains simultaneously

🎨 **Kid-Friendly Interface** - Large buttons, colorful gradients, and emoji indicators

📱 **Touchscreen Optimized** - Works great on tablets and touchscreen devices

🎮 **Multiple Control Options**
- Individual train speed sliders with color-coded gradients
- Quick action buttons (Forward, Backward, Stop)
- Global controls to command all trains at once

🔋 **Battery Monitoring** - Real-time battery level display for each train

🏷️ **Custom Naming** - Rename your trains to easily identify them

🔍 **Debug Panel** - View connection details, battery info, and command history

## Requirements

### Hardware
- Device with Bluetooth LE support
- One or more LEGO Powered Up train hubs (City, Duplo, or Powered Up sets)
- Trains must be running stock firmware (no custom firmware required)

### Software
- Python 3.9 or higher
- Tested on macOS; other platforms may require adjustments

## Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd legotrains
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Power on your LEGO trains**
   - Make sure they're within Bluetooth range
   - The hub LED should be lit

2. **Start the web app**
   ```bash
   source venv/bin/activate
   python train_webapp.py
   ```

3. **Open your browser**
   - Navigate to `http://localhost:5000`
   - Or use the IP address shown in the terminal from another device on the same network

4. **Connect to trains**
   - Click "🔗 Connect to Trains" to scan and connect
   - Click "🔍 Scan for More Trains" to add additional trains
   - The UI will automatically create control panels for each discovered train

5. **Control your trains**
   - Use the sliders for precise speed control (-100 to 100)
   - Click preset buttons for quick actions
   - Use global controls to command all trains together
   - Click "✏️ Rename" to give your trains custom names

## Interface Guide

### Speed Slider
- **Green (center)**: Stopped
- **Right side**: Forward (green gradient)
- **Left side**: Reverse (red gradient)

### Control Buttons
- **⬆️ Forward**: Set train to 50% forward speed
- **⬇️ Back**: Set train to -50% reverse speed
- **⛔ STOP**: Immediately stop the train

### Global Controls
- **⬆️⬆️ Both Forward**: All trains move forward
- **⬇️⬇️ Both Back**: All trains move backward
- **⛔⛔ STOP ALL**: Emergency stop for all trains

### Debug Panel
Click the 🔍 button in the top-right to view:
- Bluetooth addresses
- Current speed settings
- Battery levels
- Last command sent
- Raw protocol data

## Technical Details

### LEGO Powered Up Protocol
- Uses Bluetooth Low Energy (BLE) communication
- Characteristic UUID: `00001624-1212-efde-1623-785feabcd123`
- Motor port: 0x00 (Port A)
- Speed range: -100 (full reverse) to 100 (full forward)

### Architecture
- **Backend**: Flask web server with async Bluetooth handling
- **Bluetooth**: Bleak library for cross-platform BLE communication
- **Frontend**: Vanilla JavaScript with responsive CSS Grid
- **Auto-refresh**: Status updates every 3 seconds

## Project Structure

```
legotrains/
├── train_webapp.py          # Flask app and Bluetooth logic
├── templates/
│   └── index.html          # Web interface
├── venv/                   # Virtual environment (not in git)
├── .gitignore
└── README.md
```

## Troubleshooting

**Trains not appearing?**
- Ensure trains are powered on and nearby
- Check Bluetooth is enabled on your Mac
- Try scanning again with the "Scan for More Trains" button

**Connection drops?**
- Move closer to the trains
- Check battery levels (low battery can cause instability)
- Restart the web app

**Controls not working?**
- Refresh the browser page
- Check the debug panel for error messages
- Ensure the train is showing as connected (green status)

## Development

The app supports hot-reloading during development. Any changes to the HTML template will be reflected on browser refresh. Python code changes require restarting the Flask app.

## License

This project is open source. Feel free to modify and share!

## Acknowledgments

Built using the LEGO Powered Up Bluetooth protocol. Special thanks to the community for documenting the protocol specifications.

---

**Have fun controlling your LEGO trains! 🚂🎉**
