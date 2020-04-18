import os
import cv2
import numpy as np
import requests
import pyfakewebcam
from moviepy.editor import *

def get_mask(frame, bodypix_url='http://localhost:9000'):
    _, data = cv2.imencode(".jpg", frame)
    r = requests.post(
        url=bodypix_url,
        data=data.tobytes(),
        headers={'Content-Type': 'application/octet-stream'})
    mask = np.frombuffer(r.content, dtype=np.uint8)
    mask = mask.reshape((frame.shape[0], frame.shape[1]))
    return mask

def post_process_mask(mask):
    mask = cv2.dilate(mask, np.ones((10,10), np.uint8) , iterations=1)
    mask = cv2.blur(mask.astype(float), (30,30))
    return mask

def shift_image(img, dx, dy):
    img = np.roll(img, dy, axis=0)
    img = np.roll(img, dx, axis=1)
    if dy>0:
        img[:dy, :] = 0
    elif dy<0:
        img[dy:, :] = 0
    if dx>0:
        img[:, :dx] = 0
    elif dx<0:
        img[:, dx:] = 0
    return img

def hologram_effect(img):
    # add a blue tint
    holo = cv2.applyColorMap(img, cv2.COLORMAP_WINTER)
    # add a halftone effect
    bandLength, bandGap = 2, 3
    for y in range(holo.shape[0]):
        if y % (bandLength+bandGap) < bandLength:
            holo[y,:,:] = holo[y,:,:] * np.random.uniform(0.1, 0.3)
    # add some ghosting
    holo_blur = cv2.addWeighted(holo, 0.2, shift_image(holo.copy(), 5, 5), 0.8, 0)
    holo_blur = cv2.addWeighted(holo_blur, 0.4, shift_image(holo.copy(), -5, -5), 0.6, 0)
    # combine with the original color, oversaturated
    out = cv2.addWeighted(img, 0.5, holo_blur, 0.6, 0)
    return out

def get_newframe(frame, background_scaled):
    _, frame = cap.read()
    # fetch the mask with retries (the app needs to warmup and we're lazy)
    # e v e n t u a l l y c o n s i s t e n t
    mask = None
    while mask is None:
        try:
            mask = get_mask(frame)
        except:
            frame = None
            return frame
    # post-process mask and frame
    mask = post_process_mask(mask)
    frame = hologram_effect(frame)
    # composite the foreground and background
    inv_mask = 1-mask
    for c in range(frame.shape[2]):
        frame[:,:,c] = frame[:,:,c]*mask + background_scaled[:,:,c]*inv_mask
    return frame

# setup access to the *real* webcam
cap = cv2.VideoCapture('/home/juazasan/Videos/video_sin_editar.mp4')
# Define the codec and create VideoWriter object
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('/home/juazasan/Videos/output.mp4',fourcc, 30.0, (1280,720))

height, width = 720, 1280
# cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
# cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
# cap.set(cv2.CAP_PROP_FPS, 50)
# setup the fake camera
# fake = pyfakewebcam.FakeWebcam('/dev/video20', width, height)
# load the virtual background
background = cv2.imread("data/background.jpg")
background_scaled = cv2.resize(background, (width, height))
frame_read_count=0
# frames forever
while(cap.isOpened()):
    ret, frame = cap.read()
    frame_read_count = frame_read_count + 1
    if not ret:
        print('ret empty')
        break
    print('frame read')
# Release everything if job is finished
cap.release()
out.release()
cv2.destroyAllWindows()
print("frames read: " + str(frame_read_count))


