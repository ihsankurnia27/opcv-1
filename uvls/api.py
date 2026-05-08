import base64
import io
import json
import os
import sys

import cv2
import numpy as np
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from gauge_reader.find_gauge_center import find_gauge_center
from gauge_reader.find_needle_radial import find_needle_angle, draw_needle

app = FastAPI(title="Gauge Reader API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/detect")
async def detect(
    image: UploadFile = File(...),
    min_angle: float = Form(45.0),
    max_angle: float = Form(315.0),
    min_value: float = Form(0.0),
    max_value: float = Form(10.0),
    center_offset_y: float = Form(0.0),
    inner_ratio: float = Form(0.60),
    outer_ratio: float = Form(0.80),
    blur_kernel: int = Form(5),
    threshold_block: int = Form(0),
    threshold_c: int = Form(5),
    need_annotation: bool = Form(True),
):
    """Detect gauge needle position and return value + annotated image."""
    contents = await image.read()
    np_arr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if img is None:
        return {"error": "could not decode image"}

    center = find_gauge_center(img)
    if center is None:
        return {"error": "could not find gauge center"}

    cx, cy, radius = center
    # apply vertical offset (positive = down in image coords)
    cy_offset = cy + int(center_offset_y)
    angle_deg = find_needle_angle(img, cx, cy_offset, radius,
                                   inner_ratio=inner_ratio,
                                   outer_ratio=outer_ratio,
                                   blur_kernel=blur_kernel,
                                   threshold_block=threshold_block,
                                   threshold_c=threshold_c)

    # map angle to value (with wrap-around support)
    old_range = max_angle - min_angle
    new_range = max_value - min_value
    if min_angle <= max_angle:
        if old_range == 0:
            value = min_value
        else:
            value = ((angle_deg - min_angle) * new_range) / old_range + min_value
    else:
        full_range = (360 - min_angle) + max_angle
        if full_range == 0:
            value = min_value
        else:
            if angle_deg >= min_angle:
                needle_pos = angle_deg - min_angle
            else:
                needle_pos = (360 - min_angle) + angle_deg
            value = (needle_pos * new_range) / full_range + min_value
    value = max(min_value, min(max_value, value))

    annotated_b64 = None
    if need_annotation:
        annotated = draw_needle(img.copy(), cx, cy_offset, radius, angle_deg)
        _, buffer = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 85])
        annotated_b64 = base64.b64encode(buffer).decode("utf-8")

    return {
        "value": round(value, 2),
        "angle": round(angle_deg, 2),
        "center": {"x": cx, "y": cy_offset, "radius": radius},
        "annotated_image": annotated_b64,
        "error": None,
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    port = int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else 8765
    uvicorn.run(app, host="0.0.0.0", port=port)
