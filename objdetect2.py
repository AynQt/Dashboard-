import cv2
from ultralytics import YOLO
import pyttsx3
from queue import Queue
from threading import Thread

# Initialize text-to-speech engine
engine = pyttsx3.init()
engine.setProperty('rate', 150)

voice_queue = Queue()


def voice_feedback():
    while True:
        text = voice_queue.get()
        if text == "EXIT":
            break
        if not voice_queue.empty():
            engine.say(text)
            engine.runAndWait()
        voice_queue.task_done()


voice_thread = Thread(target=voice_feedback, daemon=True)
voice_thread.start()

# Load YOLOv8n model
model = YOLO('yolov8n.pt')

# Real-world object heights (meters)
# *🔹 Added more objects and their approximate heights here*
REAL_HEIGHTS = {
    'person': 1.7,
    'chair': 1.0,
    'refrigerator': 1.8,
    'car': 1.5,
    'bottle': 0.25,
    'phone': 0.15,  # Approximate height of a phone in meters
    'cup': 0.1,     # Approximate height of a cup in meters
    'laptop': 0.03, # Approximate height of a laptop in meters
    'book': 0.02,   # Approximate height of a book in meters
    'keyboard': 0.02,  # Approximate height of a keyboard in meters
    'mouse': 0.02,  # Approximate height of a computer mouse in meters
}

# *🔹 Use a properly calibrated focal length (Replace with actual calculated value)*
FOCAL_LENGTH = 294  # Adjust this value based on real-world calibration


def estimate_distance(obj_name, bbox_height):
    if bbox_height < 10:  # Ignore tiny bounding boxes
        return 50  # Assume max distance if height too small

    real_height = REAL_HEIGHTS.get(obj_name.lower(), 1.5)  # Default if unknown
    distance = (real_height * FOCAL_LENGTH) / bbox_height
    return max(0.01, round(distance, 2))  # Avoid zero or negative values


detected_objects = {}
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        print("[ERROR] Couldn't read frame from camera.")
        break

    frame = cv2.resize(frame, (800, 600))
    results = model.track(frame, persist=True, conf=0.5)  # Tracking enabled

    detected_list = []
    for r in results:
        for box in r.boxes:
            cls_id = int(box.cls[0].item())
            class_name = model.model.names[cls_id]
            bbox = box.xyxy[0].cpu().numpy()
            height = bbox[3] - bbox[1]

            if height <= 0:
                continue

            distance = estimate_distance(class_name, height)
            if distance <= 50:  # Ignore distant objects
                detected_list.append((distance, class_name, bbox))

    detected_list.sort(key=lambda x: x[0])  # Sort closest first

    for distance, class_name, bbox in detected_list:
        label = f"{class_name}: {distance:.2f}m away"
        cv2.rectangle(frame, (int(bbox[0]), int(bbox[1])), (int(bbox[2]), int(bbox[3])), (0, 255, 0), 2)
        cv2.putText(frame, label, (int(bbox[0]), int(bbox[1] - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        if class_name not in detected_objects:
            detected_objects[class_name] = {"count": 1, "distance": distance}
            voice_queue.put(f"{class_name} detected at {distance:.2f} meters.")
        else:
            prev_data = detected_objects[class_name]
            if abs(prev_data["distance"] - distance) >= 0.5:
                detected_objects[class_name] = {"count": 1, "distance": distance}
                voice_queue.put(f"{class_name} is now {distance:.2f} meters away.")

    cv2.imshow('YOLOv8n Distance Estimation', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

voice_queue.put("EXIT")
voice_thread.join()
