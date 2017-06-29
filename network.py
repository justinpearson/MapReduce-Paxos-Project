import socket, pickle, time, struct
from debug import debug

class ConnectionClosedError(Exception): pass
class KillMe(Exception): pass


def safely_close_socket(s):
    if s is None: return
    try:
        s.shutdown(socket.SHUT_RDWR)
        s.close()
    except OSError as e:
        debug('Shut down sock:',s,'caused OS Error:',e,'so prob shut it down already...')

###############################################################

def send(addr,obj,replyfn=None):
    # Pickle python object 'obj' into bytes and send to IP,Port 'addr'. 
    # Try repeatedly to connect.
    # If 'replyfn' is non-None, wait for a reply and
    # call replyfn on it.
    # If srcaddr is provided, pass it on to socket.create_connection() (DESCOPED)
    # as the source address. I use IP/port combos as authentication. (maybe bad). (DESCOPED)
    debug('Gonna try to send {} to addr {}...'.format(obj,addr))
    n = 0
    while True:
        try:
            n += 1
            debug('send:','Connecting to addr',addr,', attempt',n,'...')
            s = socket.create_connection(addr)
            break
        except ConnectionRefusedError:
            debug('send:','Cxn refused. Waiting 1 sec then trying again...')
            time.sleep(1)
    b = pickle.dumps(obj)
    debug('Outgoing obj pickled into {} bytes...'.format(len(b)))
    msg = b # no len prepended, just send the damn thing
    s.sendall(msg)
    debug('Sent {} bytes.'.format(len(msg)))
    if replyfn is not None:
        debug('Waiting for reply...')
        replyfn(s.recv(1024))  # replies aren't very long, 1024 should be sufficient.
    safely_close_socket(s)


#################################################################


def worker(ADDR,f):
    # Forever wait to accept a TCP connection on (host,port) address 'ADDR'.
    # When some bytes b arrive, hand them and the incoming addr to f(b).
    # The first 4 bytes specify the number of bytes that will follow.
    # The function f should process the bytes. 
    # The function f may return a byte-string 'replymsg', in which case this function
    # sends it back to the stream the bytes came from.
    # The function f may raise network.KillMe, in which case this function exits, safely
    # closing the socket.
    # TODO: implement an 'allowed addrs' list so that not just anyone can connect to the 
    # worker and pump jobs into it.

    print('Hi from Worker on addr',ADDR)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # http://stackoverflow.com/questions/6380057/python-binding-socket-address-already-in-use to avoid "address in use"
    sock.bind(ADDR)
    sock.listen(10) # max # queued connections
    while True:
        try:
            strm,addr = sock.accept() # blocks
        except OSError as e:
            debug('Accept error {}, quitting.'.format(e))
            safely_close_socket(sock)
            break
        debug(strm.getsockname(),'-->',strm.getpeername(),'Accepted strm from addr',addr,'!')

        # Simple: since we're using 1 TCP cxn per msg, the entire msg can be obtained
        # by just recving over and over. When the sender shutdown()'s, our recv returns b''.
        b = b''
        while True:
            tmp = strm.recv(2048) 
            if tmp == b'': break;
            else: b += tmp
        try:
            replymsg = f(b)
        except KillMe:
            strm.sendall(b'Killed me.')
            break 
        if replymsg is not None:           
            strm.sendall(replymsg)
    print('killing...')
    safely_close_socket(sock)



