"""
1. Installed on a single central machine in the same intranet.
2. Each client is configured in a server config xml file something like this
    <client ip="127.0.0.1" port="22" username="user" password="password" mail="asa@email.com">
        <alert type="memory" limit="50%"/>
        <alert type="cpu" limit="20%"/>
    </client>
3. When executed, the server script should connect to each client using ssh, upload the client script in a temp
directory, execute it and get the response.
4. After receiving the response from the client script, server script should decode it and stores it into a relational
database along with client ip. This collected data is consumed by another application, that is out of scope, but you may
design the database table yourself.
5. The server based upon the "alert" configuration of each client sends a mail notification. The notification is sent to
the client configured email address using SMTP. Use a simple text mail format with some detail about the alert. event
logs must be sent via email every time without any condition.
"""
