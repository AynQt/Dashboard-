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
        engine.say(text)
        engine.runAndWait()
        voice_queue.task_done()

voice_thread = Thread(target=voice_feedback, daemon=True)
voice_thread.start()

# Load YOLOv8n model for better accuracy
model = YOLO('yolov8n.pt')

REAL_HEIGHTS = {'person': 1.7, 'chair': 1.0, 'refrigerator': 1.8, 'car': 1.5, 'bottle': 0.25}
FOCAL_LENGTH = 600  # Adjust if needed for more precise distance

def estimate_distance(obj_name, bbox_height):
    real_height = REAL_HEIGHTS.get(obj_name.lower(), 1.5)
    return round((real_height * FOCAL_LENGTH) / bbox_height)

detected_objects = {}
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        print("[ERROR] Couldn't read frame from camera.")
        break

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

            distance = estimate_distance(class_name, height)
            if distance <= 50:
                detected_list.append((distance, class_name, bbox))

    # Prioritize objects by closest distance
    detected_list.sort(key=lambda x: x[0])

    for distance, class_name, bbox in detected_list:
        label = f"{class_name}: {distance}m away"
        cv2.rectangle(frame, (int(bbox[0]), int(bbox[1])), (int(bbox[2]), int(bbox[3])), (0, 255, 0), 2)
        cv2.putText(frame, label, (int(bbox[0]), int(bbox[1] - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        if class_name not in detected_objects:
            detected_objects[class_name] = {"count": 1, "distance": distance}
            voice_queue.put(f"{class_name} is {distance} meters from you")
        else:
            prev_data = detected_objects[class_name]
            if abs(prev_data["distance"] - distance) >= 1:
                detected_objects[class_name] = {"count": 1, "distance": distance}
                voice_queue.put(f"{class_name} is {distance} meters from you")
            elif prev_data["count"] < 3:
                detected_objects[class_name]["count"] += 1
                voice_queue.put(f"{class_name} is still {distance} meters from you")

    cv2.imshow('YOLOv8n Detection (Optimized)', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

voice_queue.put("EXIT")
voice_thread.join()
