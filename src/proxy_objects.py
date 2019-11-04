from IPython import embed
from datetime import datetime
import time
from random import randint
import inspect
import re
from autoproxy_config.config import configuration
# 1/1/2000
DEFAULT_TIMESTAMP = datetime.fromtimestamp(946684800)
BOOLEAN_VALS = (True,'1',False,'0')

QUEUE_PREFIX = configuration.app_config['redis_queue_char']['value']
PROXY_PREFIX = configuration.app_config['redis_proxy_char']['value']
DETAIL_PREFIX = configuration.app_config['redis_detail_char']['value']
class Proxy(object):
    AVAILABLE_PROTOCOLS = ('http', 'https', 'socks5', 'socks4')

    def __init__(self, address, port, protocol='http', proxy_id=None, proxy_key=None):
        self.address = address
        self.port = port
        if protocol not in self.__class__.AVAILABLE_PROTOCOLS:
            raise Exception("Invalid protocol %s" % protocol)
        self.protocol = protocol
        ifn = lambda x: int(x) if x is not None else None
        self.proxy_id = ifn(proxy_id)
        self._proxy_key = proxy_key
        

    def urlify(self):
        return "%s://%s:%s" % (self.protocol, self.address, self.port)

    def id(self):
        return self.proxy_id

    @property
    def proxy_key(self):
        if self._proxy_key is None and self.proxy_id is not None:
            self._proxy_key = "%s_%s" % (PROXY_PREFIX,self.proxy_id)
        return self._proxy_key
        
    @proxy_key.setter
    def proxy_key(self,pkey):
        self._proxy_key = pkey

    def to_dict(self):
        obj_dict = {
            "address": self.address,
            "port":  self.port,
            "protocol": self.protocol,
        }

        if self.proxy_id is not None:
            obj_dict.update({'proxy_id': self.proxy_id})
        return obj_dict

class Detail(object):
    def proxy_object_id(self,object_or_id):
        if isinstance(object_or_id,int) or object_or_id is None:
            return object_or_id
        if isinstance(object_or_id, str):
            return int(object_or_id)
        return object_or_id.id()

    def get_caller(self):
        stack = inspect.stack()
        idx=0
        #get_method = lambda idx: stack[idx][0].f_code.co_name
        
        get_class = lambda idx: re.search(r'\.(.+)\'>$',str(stack[idx][0].f_locals["self"].__class__)).group(1)
        try:
            calling_class = get_class(idx)
        except KeyError:
            return 'Detail'
        while(calling_class == 'Detail' and idx < 20):
            idx +=1
            try:
                calling_class = get_class(idx)
            except KeyError:
                return 'Detail'

        return calling_class

    def __init__(self, active=False, load_time=60000, last_updated=None, last_active=DEFAULT_TIMESTAMP, last_used=DEFAULT_TIMESTAMP, bad_count=0, blacklisted=False, blacklisted_count=0, lifetime_good=0, lifetime_bad=0, proxy_id=None, queue_id=None, detail_id=None, queue_key=None, proxy_key=None, detail_key=None):
        self._active = active
        self.load_time = load_time
        self._last_active = self.parse_timestamp(last_active)
        self._last_used = self.parse_timestamp(last_used)
        self.bad_count = bad_count
        self.blacklisted = blacklisted
        self.blacklisted_count = blacklisted_count
        self.lifetime_good = lifetime_good
        self.lifetime_bad = lifetime_bad
        
        self.proxy_id = self.proxy_object_id(proxy_id)
        self.queue_id = self.proxy_object_id(queue_id)
        self._proxy_key = proxy_key
        self._queue_key = queue_key

        ifn = lambda x: int(x) if x is not None else None
        self.detail_id = ifn(detail_id)

        self.calling_class = None
    
    @property
    def proxy_key(self):
        if self.proxy_id is not None:
            self._proxy_key = "%s_%s" % (PROXY_PREFIX,self.proxy_id)
        return self._proxy_key
        
    
    @proxy_key.setter
    def proxy_key(self,pkey):
        self._proxy_key = pkey

    @property
    def queue_key(self):
        if self.queue_id is not None:
            self._queue_key = "%s_%s" % (QUEUE_PREFIX,self.queue_id)
        return self._queue_key
            
    @queue_key.setter
    def queue_key(self,qkey):
        self._queue_key = qkey

    @property
    def detail_key(self):
        return "%s_%s_%s" % (DETAIL_PREFIX,self.queue_key,self.proxy_key)



    def id(self):
        return self.detail_id

    @property
    def active(self):
        return self.format_boolean(self.get_caller(),self._active)
    
    @active.setter
    def active(self,val):
        self._active = self.parse_boolean(val)

    @property
    def blacklisted(self):
        return self.format_boolean(self.get_caller(),self._blacklisted)
    
    @blacklisted.setter
    def blacklisted(self,val):
        self._blacklisted = self.parse_boolean(val)

    @property
    def last_active(self):
        return self.format_timestamp(self.get_caller(),self._last_active)

    @last_active.setter
    def last_active(self,val):
        self._last_active = self.parse_timestamp(val)

    @property
    def last_used(self):
        return self.format_timestamp(self.get_caller(),self._last_used)

    @last_used.setter
    def last_used(self,val):
        self._last_used = self.parse_timestamp(val)

    def format_timestamp(self,caller,val):
        if caller == 'RedisManager':
            return val.isoformat()
        return val

    def parse_timestamp(self,val):
        if type(val) is str:
            return datetime.fromisoformat(val)
        return val
    
    def format_boolean(self,caller,val):
        if caller == 'RedisManager':
            if val == True:
                return 1
            return 0
        return val

    def parse_boolean(self,val):
        if val not in BOOLEAN_VALS:
            raise Exception("Invalid value for active")
        if(val == '1'):
            val = True
        elif(val == '0'):
            val = False
        return val
            

    def to_dict(self):
        obj_dict =  {
            "active": self.active,
            "load_time": self.load_time,
            "last_used": self.last_used,
            "last_active": self.last_active,
            "bad_count": self.bad_count,
            "blacklisted": self.blacklisted,
            "blacklisted_count": self.blacklisted_count,
            "lifetime_good": self.lifetime_good,
            "lifetime_bad": self.lifetime_bad,
            
            
        }
        
        if self.detail_id is not None:
            obj_dict.update({'detail_id': self.detail_id})

        if self.proxy_id is not None:
            obj_dict.update({'proxy_id': self.proxy_id})

        if self.queue_id is not None:
            obj_dict.update({'queue_id': self.queue_id})
        return obj_dict


class Queue(object):
    def __init__(self, domain, queue_id=None, queue_key=None):
        self.domain = domain
        ifn = lambda x: int(x) if x is not None else None
        self.queue_id = ifn(queue_id)
        self._queue_key = queue_key

    def id(self):
        return self.queue_id

    @property
    def queue_key(self):
        if self._queue_key is None and self.queue_id is not None:
            self._queue_key = "%s_%s" % (QUEUE_PREFIX,self.queue_id)
        return self._queue_key
            
    @queue_key.setter
    def proxy_key(self,qkey):
        self._queue_key = qkey
    
    def to_dict(self):
        obj_dict = {
            "domain": self.domain,
        }

        if(self.queue_id is not None):
            obj_dict.update({"queue_id": self.queue_id})
        
        return obj_dict



class ProxyObject(Proxy):
    def __init__(self, proxy, queue, detail):
        if detail.proxy_id != proxy.proxy_id:
            raise Exception("Detail/Proxy mismatch on proxy id")
        if detail.queue_id != queue.queue_id:
            raise Exception("Detail/Queue mismatch on queue id")

        self.proxy = proxy
        self.queue = queue
        self.detail = detail

        self.dispatch_time = None

        super().__init__(self.proxy.address, self.proxy.port,
                         self.proxy.protocol, self.proxy.id)

    def dispatch(self):
        self.dispatch_time = datetime.now()

    def callback(self, success):
        self.detail.load_time = datetime.now() - self.dispatch_time
        self.dispatch_time = None
