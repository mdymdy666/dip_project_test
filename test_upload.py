import socket
import os

def test_upload():
    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    test_image_path = 'firstend/dist/static/img/50.a3e9ea7.jpg'
    
    with open(test_image_path, 'rb') as f:
        image_data = f.read()
    
    part1 = ('--' + boundary + '\r\nContent-Disposition: form-data; name="file"; filename="test.jpg"\r\nContent-Type: image/jpeg\r\n\r\n').encode('utf-8')
    part2 = ('\r\n--' + boundary + '--\r\n').encode('utf-8')
    request_body = part1 + image_data + part2
    
    request = ('POST /upload/50 HTTP/1.1\r\nHost: 127.0.0.1:5000\r\nContent-Type: multipart/form-data; boundary=' + boundary + '\r\nContent-Length: ' + str(len(request_body)) + '\r\n\r\n').encode('utf-8') + request_body
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('127.0.0.1', 5000))
    s.sendall(request)
    
    response = b''
    while True:
        data = s.recv(4096)
        if not data:
            break
        response += data
    
    s.close()
    print('Response:', response.decode('utf-8', errors='replace'))

if __name__ == '__main__':
    test_upload()
