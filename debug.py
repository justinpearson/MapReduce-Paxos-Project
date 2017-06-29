import time

DEBUG = False

if DEBUG:
    def debug(*s): print('[t={}]'.format(time.time()),*s)
else:
    def debug(*s): pass
