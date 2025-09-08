# sentinel.py
import socket

def qwen_mutate(task):
    s = socket.socket()
    s.connect(("localhost", 9090))
    s.send(task.encode())
    response = s.recv(8192).decode()
    return response

# Example usage
mutation = qwen_mutate("Scaffold a Rust module for audio playback using rodio.")
print(mutation)

