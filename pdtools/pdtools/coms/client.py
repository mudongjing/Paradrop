'''
Client-side tools for communicating with a server using RPC
'''

from twisted.web.xmlrpc import Proxy


class RpcClient:

    '''
    Remote client RPC wrapper. Translates seemingly local calls
    into remote RPC calls to the given server. 

    Usage: 
        client = RpcClient("https://something:70234")
        call = client.nameOfRemoteCall(arg1 arg2)
        call.addCallbacks(aCallback)


    Calls to this object always return deferreds. 
    '''

    def __init__(self, urlAndPort):
        self.proxy = Proxy(urlAndPort, allowNone=True)

    def __getattr__(self, item):
        def wrap(*args):
            return self.proxy.callRemote(item, *args)

        return wrap
