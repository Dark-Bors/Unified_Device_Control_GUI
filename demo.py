# dual_open_test.py
import cv2, sys, time

IDX_A = int(sys.argv[1]) if len(sys.argv) > 1 else 1
IDX_B = int(sys.argv[2]) if len(sys.argv) > 2 else 2
BE_A  = (sys.argv[3] if len(sys.argv) > 3 else "dshow").lower()  # dshow|msmf
BE_B  = (sys.argv[4] if len(sys.argv) > 4 else "dshow").lower()

def beflag(name):
    return cv2.CAP_DSHOW if name=="dshow" else (cv2.CAP_MSMF if name=="msmf" else 0)

def open_cam(idx, be):
    cap = cv2.VideoCapture(idx, beflag(be))
    t0=time.time()
    while not cap.isOpened() and time.time()-t0<2: time.sleep(0.05)
    if not cap.isOpened(): return None
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 15.0)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    # warmup
    for _ in range(6):
        ok,_ = cap.read()
        if ok: break
        time.sleep(0.05)
    return cap

capA = open_cam(IDX_A, BE_A)
capB = open_cam(IDX_B, BE_B)
print(f"A({IDX_A},{BE_A}) open:", bool(capA), "  B({IDX_B},{BE_B}) open:", bool(capB))
if not capA or not capB:
    print("Try pairs like: 1 2 dshow msmf  |  1 2 msmf dshow  |  0 1 dshow dshow  |  0 2 dshow dshow")
    if capA: capA.release()
    if capB: capB.release()
    sys.exit(1)

while True:
    okA, fA = capA.read()
    okB, fB = capB.read()
    if okA: cv2.imshow("CamA", fA)
    if okB: cv2.imshow("CamB", fB)

    # allow closing either window or pressing Esc/Q
    if (cv2.getWindowProperty("CamA", cv2.WND_PROP_VISIBLE) < 1) or \
       (cv2.getWindowProperty("CamB", cv2.WND_PROP_VISIBLE) < 1):
        break
    k = cv2.waitKey(1) & 0xFF
    if k in (27, ord('q'), ord('Q')):
        break

capA.release(); capB.release(); cv2.destroyAllWindows()
