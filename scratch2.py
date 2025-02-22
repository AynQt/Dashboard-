import cv2
from ultralytics import YOLO
import pyttsx3
import time
from queue import Queue
from threading import Thread

# ✅ Initialize Text-to-Speech Engine (Fixed)
engine = pyttsx3.init()
engine.setProperty('rate', 150)

voice_queue = Queue()


def voice_feedback():
    """ Continuously process the voice queue. """
    while True:
        text = voice_queue.get()
        if text == "EXIT":
            break
        engine.say(text)
        engine.runAndWait()
        voice_queue.task_done()


# ✅ Start the voice assistant in a separate thread
voice_thread = Thread(target=voice_feedback, daemon=True)
voice_thread.start()

# ✅ Load YOLOv8 model
model = YOLO('yolov8n.pt')

# ✅ Real-world object heights (meters)
REAL_HEIGHTS = {'person': 1.7, 'chair': 1.0, 'refrigerator': 1.8, 'car': 1.5, 'bottle': 0.25}

# ✅ Approximate focal length (Adjust this for your camera)
FOCAL_LENGTH = 350  # 🚀 Try values between 300-400 for webcams


def estimate_distance(obj_name, bbox_height):
    """ Estimate distance using known object height and bounding box height. """
    if bbox_height < 10:  # Ignore tiny bounding boxes
        return 5000  # Assume far distance

    real_height = REAL_HEIGHTS.get(obj_name.lower(), 1.5)  # Default to 1.5m if unknown
    distance_m = (real_height * FOCAL_LENGTH) / bbox_height
    return max(0.1, round(distance_m, 2))  # Avoid negative values, round to 2 decimal places


detected_objects = {}  # Store detected object distances

# ✅ Try opening the camera safely
cap = cv2.VideoCapture(0)
start_time = time.time()

while True:
    ret, frame = cap.read()
    if not ret:
        print("[ERROR] Couldn't read frame from camera.")
        if time.time() - start_time > 5:  # 🚀 Timeout: Exit after 5 seconds if camera fails
            break
        continue

    frame = cv2.resize(frame, (800, 600))
    results = model(frame)

    detected_list = []
    for r in results:
        for box in r.boxes:
            cls_id = int(box.cls[0].item())
            class_name = model.model.names[cls_id]
            bbox = box.xyxy[0].cpu().numpy()
            height = bbox[3] - bbox[1]

            if height <= 0:
                continue

            distance_m = estimate_distance(class_name, height)
            if distance_m <= 50:  # 🚀 Ignore objects farther than 50m
                detected_list.append((distance_m, class_name, bbox))

    detected_list.sort(key=lambda x: x[0])  # Sort closest first

    for distance_m, class_name, bbox in detected_list:
        distance_cm = round(distance_m * 100)  # Convert meters to cm
        label = f"{class_name}: {distance_m:.2f}m ({distance_cm} cm) away"

        cv2.rectangle(frame, (int(bbox[0]), int(bbox[1])), (int(bbox[2]), int(bbox[3])), (0, 255, 0), 2)
        cv2.putText(frame, label, (int(bbox[0]), int(bbox[1] - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        # ✅ Optimized voice feedback logic
        if class_name not in detected_objects:
            detected_objects[class_name] = {"count": 1, "distance": distance_cm}
            voice_queue.put(f"{class_name} detected at {distance_cm} centimeters away.")
        else:
            prev_data = detected_objects[class_name]
            if abs(prev_data["distance"] - distance_cm) >= 50:
                detected_objects[class_name] = {"count": 1, "distance": distance_cm}
                voice_queue.put(f"{class_name} is now {distance_cm} centimeters away.")

    cv2.imshow('YOLOv8n Distance Estimation', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

# ✅ Safely stop the voice assistant thread
voice_queue.put("EXIT")
voice_thread.join()
