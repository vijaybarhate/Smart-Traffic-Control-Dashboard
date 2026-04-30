import os
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import threading
import time
import logging
import random

# Optional OpenCV import for environments that support it
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

# Configure Flask to serve the static 'dist' directory created by Vite
app = Flask(__name__, static_folder='dist', static_url_path='/')
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
traffic_counts = {"north": 12, "south": 8, "east": 15, "west": 6}
traffic_counts_lock = threading.Lock()
current_signal = "north"
manual_override = False
signal_timer = time.time()
detection_active = False
video_source = "intersection.mp4"

# AI Traffic Control Parameters
MAX_GREEN_TIME = 30  # seconds
MIN_GREEN_TIME = 8   # seconds
HIGH_TRAFFIC_THRESHOLD = 15
LOW_TRAFFIC_THRESHOLD = 3

class VehicleDetector:
    def __init__(self, source="intersection.mp4"):
        if OPENCV_AVAILABLE:
            self.cap = cv2.VideoCapture(source)
            if not self.cap.isOpened():
                raise ValueError("Could not open video source")
            self.background_subtractor = cv2.createBackgroundSubtractorMOG2(
                history=500, varThreshold=50, detectShadows=True
            )
            self.min_contour_area = 500
        else:
            raise ImportError("OpenCV not available")
            
    def detect_vehicles_in_frame(self, frame):
        fg_mask = self.background_subtractor.apply(frame)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        height, width = frame.shape[:2]
        center_x, center_y = width // 2, height // 2
        region_counts = {"north": 0, "south": 0, "east": 0, "west": 0}
        
        for contour in contours:
            if cv2.contourArea(contour) > self.min_contour_area:
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    if cy < center_y - 50: region_counts["north"] += 1
                    elif cy > center_y + 50: region_counts["south"] += 1
                    elif cx < center_x - 50: region_counts["west"] += 1
                    elif cx > center_x + 50: region_counts["east"] += 1
        return region_counts

def ai_signal_controller():
    """AI-based signal timing logic"""
    global current_signal, signal_timer, traffic_counts, manual_override
    
    if manual_override:
        return
    
    with traffic_counts_lock:
        time_since_change = time.time() - signal_timer
        current_count = traffic_counts[current_signal]
        max_traffic_dir = max(traffic_counts, key=traffic_counts.get)
        max_traffic_count = traffic_counts[max_traffic_dir]
        should_switch = False
        new_signal = current_signal
        
        if time_since_change > MAX_GREEN_TIME:
            should_switch = True
            new_signal = max_traffic_dir
        elif (time_since_change > MIN_GREEN_TIME and 
              current_count < LOW_TRAFFIC_THRESHOLD and 
              max_traffic_count > HIGH_TRAFFIC_THRESHOLD and
              max_traffic_dir != current_signal):
            should_switch = True
            new_signal = max_traffic_dir
        elif (max_traffic_count > HIGH_TRAFFIC_THRESHOLD * 2 and 
              max_traffic_dir != current_signal and
              time_since_change > MIN_GREEN_TIME // 2):
            should_switch = True
            new_signal = max_traffic_dir
            
        if should_switch:
            current_signal = new_signal
            signal_timer = time.time()

def detection_thread():
    """Main detection and control loop, safe fallback to simulation"""
    global traffic_counts, detection_active
    detection_active = True
    
    use_simulation = False
    detector = None
    
    if OPENCV_AVAILABLE and os.path.exists(video_source):
        try:
            detector = VehicleDetector(video_source)
            logger.info("Started real video detection.")
        except Exception as e:
            logger.warning(f"Failed to load video: {e}. Falling back to simulation.")
            use_simulation = True
    else:
        logger.info("OpenCV or video file missing. Using simulated traffic data.")
        use_simulation = True

    while detection_active:
        try:
            if not use_simulation:
                ret, frame = detector.cap.read()
                if not ret:
                    detector.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                region_counts = detector.detect_vehicles_in_frame(frame)
                with traffic_counts_lock:
                    for d in traffic_counts:
                        traffic_counts[d] = int(0.7 * traffic_counts[d] + 0.3 * region_counts[d])
            else:
                # Realistic Simulation Logic
                with traffic_counts_lock:
                    for d in traffic_counts:
                        if d == current_signal and not manual_override:
                            # Cars leave intersection smoothly
                            traffic_counts[d] = max(0, traffic_counts[d] - random.randint(1, 4))
                        else:
                            # Cars arrive and build up
                            traffic_counts[d] = min(40, traffic_counts[d] + random.randint(0, 2))
                time.sleep(0.5) 
            
            ai_signal_controller()
            
            if not use_simulation:
                time.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Detection loop error: {e}")
            time.sleep(1)
            
    if detector and hasattr(detector, 'cap'):
        detector.cap.release()

# --- Serve React Frontend ---
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    # Serve static assets from 'dist' directory
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        # Fallback to index.html for React Router
        if os.path.exists(os.path.join(app.static_folder, 'index.html')):
            return send_from_directory(app.static_folder, 'index.html')
        else:
            return jsonify({"error": "Dashboard not built. Run 'npm run build'."}), 500

# --- API Routes ---
@app.route("/api/get_counts")
def get_counts():
    with traffic_counts_lock:
        current_counts = traffic_counts.copy()
    response = {
        "counts": current_counts,
        "signal": current_signal,
        "manual_override": manual_override,
        "timestamp": time.time(),
        "total_vehicles": sum(current_counts.values())
    }
    return jsonify(response)

@app.route("/api/set_signal/<direction>", methods=['GET', 'POST'])
def set_signal(direction):
    global current_signal, manual_override, signal_timer
    valid_directions = ["north", "south", "east", "west"]
    if direction.lower() not in valid_directions:
        return jsonify({"status": "error", "message": "Invalid direction"}), 400
    with traffic_counts_lock:
        current_signal = direction.lower()
        manual_override = True
        signal_timer = time.time()
    return jsonify({"status": "success", "current_signal": current_signal})

@app.route("/api/end_override", methods=['GET', 'POST'])
def end_override():
    global manual_override
    manual_override = False
    return jsonify({"status": "success"})

@app.route("/api/system_status")
def system_status():
    return jsonify({
        "detection_active": detection_active,
        "manual_override": manual_override,
        "current_signal": current_signal,
        "total_vehicles": sum(traffic_counts.values())
    })

if __name__ == "__main__":
    t = threading.Thread(target=detection_thread, daemon=True)
    t.start()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
