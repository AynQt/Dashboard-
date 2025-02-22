import cv2
from ultralytics import YOLO
import pyttsx3
from queue import Queue
from threading import Thread

# ✅ Initialize Text-to-Speech Engine (Slower for clarity)
engine = pyttsx3.init()
engine.setProperty('rate', 110)  # Slow speech speed for clarity

voice_queue = Queue()


def voice_feedback():
    """ Continuously process the voice queue. """
    while True:
        text = voice_queue.get()
        if text == "EXIT":
            break
        if text:  # Ensure non-empty speech
            engine.say(text)
            engine.runAndWait()
        voice_queue.task_done()


# ✅ Start the voice assistant thread
voice_thread = Thread(target=voice_feedback, daemon=True)
voice_thread.start()

# ✅ Load YOLOv8 model (Using `conf=0.5` for more accurate detection)
model = YOLO('yolov8n.pt')

# ✅ Real-world object heights (meters)
REAL_HEIGHTS = {
    'person': 1.7, 'chair': 1.0, 'refrigerator': 1.8, 'car': 1.5,
    'bottle': 0.25, 'tv': 0.6, 'laptop': 0.3, 'cup': 0.12
}

# ✅ Properly calibrated focal length (Tweak if needed)
FOCAL_LENGTH = 350  # Adjust within 300-400 range for best accuracy


def estimate_distance(obj_name, bbox_height):
    """ Estimate distance using known object height and bounding box height. """
    if bbox_height < 10:  # Ignore tiny bounding boxes
        return 50  # Assume max distance

    real_height = REAL_HEIGHTS.get(obj_name.lower(), 1.5)  # Default height if unknown
    distance = (real_height * FOCAL_LENGTH) / bbox_height
    return max(0.1, round(distance, 2))  # Avoid zero/negative values


detected_objects = {}  # Store detected objects
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        print("[ERROR] Couldn't read frame from camera.")
        break

    frame = cv2.resize(frame, (800, 600))
    results = model.track(frame, persist=True, conf=0.5, iou=0.45)  # Increased confidence & IoU

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
            if distance <= 50:  # Ignore objects farther than 50m
                detected_list.append((distance, class_name, bbox))

    detected_list.sort(key=lambda x: x[0])  # Sort by closest first

    for distance, class_name, bbox in detected_list:
        label = f"{class_name}: {distance:.2f}m away"
        cv2.rectangle(frame, (int(bbox[0]), int(bbox[1])), (int(bbox[2]), int(bbox[3])), (0, 255, 0), 2)
        cv2.putText(frame, label, (int(bbox[0]), int(bbox[1] - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        # ✅ Optimized voice feedback logic (Ignore humans in speech)
        if class_name.lower() == 'person':
            continue  # Skip humans in voice feedback

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

# ✅ Safely stop the voice assistant thread
voice_queue.put("EXIT")
voice_thread.join()
