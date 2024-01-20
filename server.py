import socket
import threading
import pickle, struct
from sys import getsizeof


IP = socket.gethostbyname(socket.gethostname())
VIDEO_PORT = 8000
VIDEO_ADDR = (IP, VIDEO_PORT)
AUDIO_PORT = 8001
AUDIO_ADDR = (IP, AUDIO_PORT)
GENERAL_PORT = 8002
GENERAL_ADDR = (IP, GENERAL_PORT)
FORMAT = 'utf-8'
VIDEO_CHUNK_SIZE = 1024*2500
AUDIO_CHUNK_SIZE = 1024*3
GENERAL_CHUNK_SIZE = 512

videos_dict = {}
audio_dict = {}
general_dict = {}
threads = []

######################################################## VIDEO SERVER ########################################################
video_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
video_server.bind(VIDEO_ADDR)
video_server.listen(1)
print(f"[ VIDEO SERVER STARTED ON : {VIDEO_ADDR} ]")
         
def accept_video_connections():
    while True:
        new_conn, addr = video_server.accept()
        print(f"NEW VIDEO CONNECTION : {addr}, {threading.active_count()}")
        recv_video_thread = threading.Thread(target=recv_video, args=(new_conn, addr))
        recv_video_thread.start()
        threads.append(recv_video_thread)

accept_video_conns = threading.Thread(target=accept_video_connections)
accept_video_conns.start()
threads.append(accept_video_conns)

def recv_video(new_conn, addr):
    global videos_dict
    connection = True

    try:
        data = new_conn.recv(1024)
        data = pickle.loads(data)
        print(data)
        username = data['username']
        meet_id = data["meet_id"]
        if meet_id in videos_dict.keys():
            videos_dict[meet_id].append(((new_conn, addr), username))
        else:
            videos_dict[meet_id] = [((new_conn, addr), username)]

    except Exception as e:
        # print(addr, e)
        pass

    while connection:
        try:
            data = new_conn.recv(VIDEO_CHUNK_SIZE)
            # print(addr, getsizeof(data))
            for client in videos_dict[meet_id]:
                if client[0][1]!= addr:
                    client[0][0].send(data)

        except socket.error as s_err:
            if s_err.errno == 10054:
                for i, client in enumerate(videos_dict[meet_id]):
                    if addr == client[0][1]:
                        videos_dict[meet_id].pop(i)
                new_conn.close()
                print(f"{addr} DISCONNECTED...")
                connection = False

        except Exception as e:
            # print("1", addr, e)
            pass




######################################################## AUDIO SERVER ########################################################
audio_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
audio_server.bind(AUDIO_ADDR)
audio_server.listen(2)
print(f"[ AUDIO SERVER STARTED ON : {AUDIO_ADDR} ]")

def accept_audio_connections():
    while True:
        new_conn, addr = audio_server.accept()
        print(f"NEW AUDIO CONNECTION : {addr}.")
        recv_audio_thread = threading.Thread(target=recv_audio, args=(new_conn, addr))
        recv_audio_thread.start()
        threads.append(recv_audio_thread)

accept_audio_conns = threading.Thread(target=accept_audio_connections)
accept_audio_conns.start()
threads.append(accept_audio_conns)

def recv_audio(new_conn, addr):
    global audio_dict
    connection = True

    try:
        data = new_conn.recv(1024)
        data = pickle.loads(data)
        print(data)
        username = data['username']
        meet_id = data["meet_id"]
        if meet_id in audio_dict.keys():
            audio_dict[meet_id].append(((new_conn, addr), username))
        else:
            audio_dict[meet_id] = [((new_conn, addr), username)]

    except Exception as e:
        # print(addr, e)
        pass

    while connection:
        try:
            
            data = new_conn.recv(AUDIO_CHUNK_SIZE)
            # print(getsizeof(data))

            for client in audio_dict[meet_id]:
                if client[0][1]!= addr:
                    client[0][0].sendall(data)

        except socket.error as s_err:
            if s_err.errno == 10054:
                # data = {"username":username, "connection":False}
                for i, client in enumerate(audio_dict[meet_id]):
                    if addr == client[0][1]:
                        audio_dict[meet_id].pop(i)
                    # else:
                    #     client[0][0].sendall(pickle.dumps(data))
                new_conn.close()
                print(f"{addr} DISCONNECTED...")
                connection = False

        except Exception as e:
            # print("2", addr, e)
            pass



######################################################## GENERAL SERVER ########################################################
general_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
general_server.bind(GENERAL_ADDR)
general_server.listen(2)
print(f"[ GENERAL SERVER STARTED ON : {GENERAL_ADDR} ]")

def accept_general_connections():
    while True:
        new_conn, addr = general_server.accept()
        print(f"NEW GENERAL CONNECTION : {addr}.")
        general_recv_thread = threading.Thread(target=general_recv, args=(new_conn, addr))
        general_recv_thread.start()
        threads.append(general_recv_thread)

accept_general_conns = threading.Thread(target=accept_general_connections)
accept_general_conns.start()
threads.append(accept_general_conns)

def general_recv(new_conn, addr):
    global general_dict
    connection = True

    # --------------------------------- FOR LICENSING --------------------------------- #

    while True:
        # print("e, p")
        data = new_conn.recv(1024)
        data = pickle.loads(data)
        username = data['username']
        email = data['email']
        password = data['password']
        domain = email[-13:]
        if domain == '@iiitdm.ac.in':
            new_conn.send(b'1')
            break
        new_conn.send(b'0')

    while True:
        # print("m")
        data = new_conn.recv(1024)
        data = pickle.loads(data)
        username = data['username']
        meet_id = data['meet_id']
        if meet_id in general_dict.keys():
            if username in general_dict[meet_id]:
                new_conn.send(b'0')
                continue
        new_conn.send(b'1')
        break

        # --------------------------------------------------------------------------------- #

    try:
        data = new_conn.recv(1024)
        data = pickle.loads(data)
        print(data)
        username = data['username']
        meet_id = data["meet_id"]
        if meet_id in general_dict.keys():
            general_dict[meet_id].append(((new_conn, addr), username))
        else:
            general_dict[meet_id] = [((new_conn, addr), username)]

    except Exception as e:
        # print(addr, e)
        pass

    while connection:
        try:
            
            data = new_conn.recv(GENERAL_CHUNK_SIZE)
            print(getsizeof(data))
            if data:
                temp = pickle.loads(data)
                print(temp)
                to = temp.get("to", "send-all")
                msg_type = temp.get("msg_type", "send-msg")

                
                if to == "send-all":
                    for client in general_dict[meet_id]:
                        if client[0][1]!= addr:
                            print("sending msg to ", client[1])
                            client[0][0].send(data)
                elif to == "send-usernames":
                    selected_users = temp.get("selected_users", [])
                    for client in general_dict[meet_id]:
                        if client[1] in selected_users:
                            print("sending msg to ", client[1])
                            client[0][0].send(data)

                if msg_type == "send-file":
                    file_size = temp.get("size_of_file", 0)
                    print("In send-file, size: ", file_size)
                    
                    count = 0
                    # file_size += GENERAL_CHUNK_SIZE
                    while file_size > 0:
                        file_data = new_conn.recv(GENERAL_CHUNK_SIZE)
                        file_size -= len(file_data)

                        # print("Recieved, len", getsizeof(file_data), len(file_data), count)
                        # count += 1
                        # print("Size left: ", file_size)

                        if to == "send-all":
                            for client in general_dict[meet_id]:
                                if client[0][1]!= addr:
                                    # print("sending file to ", client[1])
                                    client[0][0].sendall(file_data)
                        elif to == "send-usernames":
                            selected_users = temp.get("selected_users", [])
                            for client in general_dict[meet_id]:
                                if client[1] in selected_users:
                                    # print("sending file to ", client[1])
                                    client[0][0].sendall(file_data)

                        if not file_data:
                            print("Server: file End")
                            break

                    print("file sent")

        except socket.error as s_err:
            if s_err.errno == 10054:
                # data = {"username":username, "connection":False}
                for i, client in enumerate(general_dict[meet_id]):
                    if addr == client[0][1]:
                        general_dict[meet_id].pop(i)
                    # else:
                    #     client[0][0].sendall(pickle.dumps(data))
                new_conn.close()
                print(f"{addr} DISCONNECTED...")
                connection = False

        except Exception as e:
            # print("3", addr, e)
            pass



for thread in threads:
    thread.join()
