from flask import Flask, render_template, Response, request, url_for, jsonify
import cv2, pyaudio
import socket, pickle, threading, os, signal, time
from sys import getsizeof, exit
from os.path import getsize as getfile_size

IP = socket.gethostbyname(socket.gethostname())
VIDEO_PORT = 8000
VIDEO_ADDR = (IP, VIDEO_PORT)
AUDIO_PORT = 8001
AUDIO_ADDR = (IP, AUDIO_PORT)
GENERAL_PORT = 8002
GENERAL_ADDR = (IP, GENERAL_PORT)
STRING_FORMAT = 'utf-8'

# VIDEO
VIDEO_CHUNK_SIZE = 1024*2500
FRAME_WIDTH = 250
FRAME_HEIGHT = 200

# AUDIO
AUDIO_FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
AUDIO_FRAME_RATE = 1024
AUDIO_CHUNK_SIZE = 1024*3

# GENERAL
GENERAL_CHUNK_SIZE = 512

username = ""
password = ""
meet_id = ""
screens = {}
messages = []


app = Flask(__name__, static_url_path='/static')

def disconnect_sockets():
    global video_socket, audio_socket, general_socket, cap, stream
    cap.release()
    stream.close()
    if video_socket:
        print("DISCONNECTING VIDEO SOCKET...")
        video_socket.close()
    if audio_socket:
        print("DISCONNECTING AUDIO SOCKET...")
        audio_socket.close()
    if general_socket:
        print("DISCONNECTING GENERAL SOCKET...")
        general_socket.close()
    exit(0)

def recv_video():
    global screens
    while True:
        try:
            data = video_socket.recv(VIDEO_CHUNK_SIZE)
            # print(getsizeof(data))
            if len(data) <=0: continue
            data = pickle.loads(data)
            user = data["username"]
            frame = data["frame"]
            screens[user] = frame

        except OSError as e:
            if e.winerror == 10038 or e.winerror == 10054:
                disconnect_sockets()
                break

        except Exception as e:
            # print("4", e)
            pass


def get_other_videos(user_name):
    global screens
    while True:
        if user_name in screens.keys():
            yield (b'--frame\r\n'
                        b'Content-Type: image/jpeg\r\n\r\n' + screens[user_name] + b'\r\n')
    

def capture_user_video():
    global cap, cameraOn
    while cameraOn:
        if not cap.isOpened():
            print("Cap closed")
            cap.open(0)
        while cap.isOpened():
            ret, frame = cap.read()
            if ret:
                frame = cv2.flip(frame, 1)
                frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))

                frame = cv2.imencode('.jpg', frame)[1].tobytes()

                data = pickle.dumps({"username": username, "frame":frame})
                try:
                    video_socket.sendall(data)
                except OSError as e:
                    if e.winerror == 10038 or e.winerror == 10054:
                        print("error in capture user video")
                        cameraOn = False
                        disconnect_sockets()
                        break
                
                # print(getsizeof(frame))
                yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        print("Cap isOpened: ", cap.isOpened())
    print("Cap: ", cap,"CameraOn: ", cameraOn)

        
        

def send_user_audio():
    global stream, audio_semaphore, micOn
    while True:
        audio_semaphore.acquire()
        while micOn:
            try:
                data = stream.read(AUDIO_FRAME_RATE)
                pickled_data = pickle.dumps({"username": username, "audio":data})
                audio_socket.sendall( pickled_data)
            except OSError as e:
                if e.winerror == 10038 or e.winerror == 10054:
                    disconnect_sockets()
                    break

            except Exception as e:
                # print("errror in sernd user audio", e)
                pass
        
        audio_semaphore.release()


def recv_audio():
    global stream, speakerOn
    while True:
        try:
            data = audio_socket.recv(AUDIO_CHUNK_SIZE)
            data = pickle.loads(data)
            user = data["username"]
            peer_audio = data.get("audio", "")
        
            if speakerOn and peer_audio:
                stream.write(peer_audio, AUDIO_FRAME_RATE)
            
        except OSError as e:
            if e.winerror == 10038 or e.winerror == 10054:
                disconnect_sockets()
                break

        except Exception as e:
            # print("2", e)
            pass



def general_recv():
    global messages
    while True:
        try:
            data = general_socket.recv(GENERAL_CHUNK_SIZE)
            data = pickle.loads(data)
            from_user = data["username"]
            peer_msg = data.get("msg", "")
            msg_type = data.get("msg_type", "send-msg")
            
            if msg_type == "send-msg":
                messages.append({"username":from_user, "msg":peer_msg})
            elif msg_type == "send-file":
                file_size = data.get("size_of_file", 0)
                print("file size: ", file_size)
                

                with open(peer_msg, "wb") as file:
                    while file_size > 0:
                        chunk = general_socket.recv(GENERAL_CHUNK_SIZE)
                        file_size -= len(chunk)
                        # print(getsizeof(chunk))
                        file.write(chunk)
                print("file Created")
                
            
        except OSError as e:
            if e.winerror == 10038 or e.winerror == 10054:
                disconnect_sockets()
                break

        except Exception as e:
            # print("error in general recv", e)
            pass

#---------------------------------------- HOME ROUTE ----------------------------------------

@app.route('/')
def index():
    global cap, cameraOn, micOn
    global camera_off_url, camera_on_url, mic_off_url, mic_on_url, speaker_on_url, speaker_off_url
    camera_on_url = url_for('static', filename='images/cameraOn.png')
    camera_off_url = url_for('static', filename='images/cameraOff.png')
    mic_on_url = url_for('static', filename='images/micOn.png')
    mic_off_url = url_for('static', filename='images/micOff.png')
    speaker_on_url = url_for('static', filename='images/speakerOn.png')
    speaker_off_url = url_for('static', filename='images/speakerOff.png')
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cameraOn = True
    return render_template('index.html')

#---------------------------------------- VIDEO ROUTES ----------------------------------------

@app.route('/user_video')
def user_video():
    # Return the response generated along with the specific media type (mime type)
    return Response(capture_user_video(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed/<user_name>')
def video_feed(user_name):
    # Return the response generated along with the specific media type (mime type)
    return Response(get_other_videos(user_name), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/clients', methods = ['POST'])
def handle_posts():
    global screens, audio_semaphore, micOn, cap, cameraOn, speakerOn, messages
    reqBody = request.get_json()
    action = reqBody.get("action", "")

    if action == "clients":
        x = jsonify({"users":list(screens.keys()) , "messages":messages})
        messages = []
        return x
    
    elif action == "audioButton":
        audio_button = None
        if micOn == True:
            micOn = False
            audio_button =  mic_off_url
            audio_semaphore.acquire()
            print("Mic stop/aquire")
        else:
            micOn = True
            audio_button =  mic_on_url
            audio_semaphore.release()
            print("Mic on/release")
        
        return jsonify({"audio_button":audio_button})
    
    elif action == "videoButton":
        user_video = None
        video_button = None
        if cameraOn:
            cameraOn = False
            user_video =  url_for('static', filename='images/user.png')
            video_button =  camera_off_url
            cap.release()
        else:
            cameraOn = True
            user_video =  url_for(f'user_video') 
            video_button =  camera_on_url
            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        print(cameraOn)
        return jsonify({"user_video":user_video, "video_button":video_button})
    
    elif action == "speakerButton":
        speaker_button = None
        if speakerOn:
            speakerOn = False
            speaker_button = speaker_off_url
        else:
            speakerOn = True
            speaker_button = speaker_on_url
    return jsonify({"speaker_button": speaker_button})

@app.route('/msgs', methods =['POST'])
def handle_msg_posts():
    reqBody = request.get_json()
    print(reqBody)
    msg_type = reqBody.get("msg_type", "send-msg")
    msg = reqBody.get("msg", "")

    try:
        if msg_type == "send-msg":
            x = pickle.dumps(reqBody | {"username":username})
            print(getsizeof(x), reqBody | {"username":username})
            general_socket.sendall(x)
        elif msg_type == "send-file":
            general_socket.send(pickle.dumps(reqBody | {"username":username, "size_of_file":getfile_size(msg)}))
            print("size of file: ", getfile_size(msg))
            # count = 0
            with open(msg, "rb") as file:
                while True:
                    file_data = file.read(GENERAL_CHUNK_SIZE)
                    general_socket.sendall(file_data)
                    # print(getsizeof(file_data))
                    # print(msg, count)
                    # count += 1
                    if not file_data:
                        print("File End")
                        break

                print("File Sent")
        return Response(status=204)
                
    except OSError as e:
        if e.winerror == 10038 or e.winerror == 10054:
            disconnect_sockets()

    except Exception as e:
        # print("in handle posts", e)        
        pass

#---------------------------------------- APP ----------------------------------------


def connect_to_servers():
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':  # check if it's the main process
        print("connecting...")

        #----- Socket Creation -----#
        global video_socket, audio_socket, general_socket, username, meet_id, password

        video_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        video_socket.connect(VIDEO_ADDR)
        

        audio_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        audio_socket.connect(AUDIO_ADDR)
        

        general_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        general_socket.connect(GENERAL_ADDR)

        # --------------------------------- FOR LICENSING --------------------------------- #
        time.sleep(0.1)
        while True:
            email = input("Enter a valid email: ")
            # email = "uday@iiitdm.ac.in"
            username = email[:len(email)-13]
            password = input("Password: ")
            # password = "123"

            data = pickle.dumps({"email":email, "username":username, "password":password})
            general_socket.send(data)
            res = general_socket.recv(4)
            if res == b'0':
                print("Invalid License. Try another Licensed Email.")
            else:
                break

        while True:
            meet_id = input("Enter Meet Id: ")
            # meet_id = "abc"
            general_socket.send(pickle.dumps({"email":email, "username":username, "meet_id": meet_id}))
            res = general_socket.recv(4)
            if res == b'0':
                print("Email id already present in Meet! Use another licensed email id.")
            else:
                break
        # ----------------------------------------------------------------- #

        data = pickle.dumps({"username":username, "meet_id":meet_id})
        video_socket.send(data)
        audio_socket.send(data)
        general_socket.send(data)

        global audio, stream
        audio = pyaudio.PyAudio()
        stream = audio.open(format=AUDIO_FORMAT, channels=CHANNELS, rate=RATE, input=True, output=True, frames_per_buffer=AUDIO_FRAME_RATE)

        global audio_semaphore, micOn, speakerOn
        audio_semaphore = threading.Semaphore(1)
        micOn = False
        speakerOn = True
        audio_semaphore.acquire()

        #----- Threads -----#
        recv_video_thread = threading.Thread(target=recv_video)
        recv_video_thread.start()

        send_audio_thread = threading.Thread(target=send_user_audio)
        send_audio_thread.start()

        recv_audio_thread = threading.Thread(target=recv_audio)
        recv_audio_thread.start()

        recv_general_thread = threading.Thread(target=general_recv)
        recv_general_thread.start()

def signal_handler(signal, frame):
    global cap, stream
    print('You pressed Ctrl+C!')
    disconnect_sockets()
    exit(0)

signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    threading.Thread(target=connect_to_servers).start()
    app.run(debug=True)