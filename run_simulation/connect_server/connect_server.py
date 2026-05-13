import xmlrpc.client

def connect_server(port: int) -> tuple[xmlrpc.client.ServerProxy, str]:
    """
    Connects to the server and returns the server object and the server address.
    """
    server = xmlrpc.client.ServerProxy(f"http://localhost:{port}")
    server_address = f"http://localhost:{port}"
    return server, server_address