# The bUrDP socket protocol

The protocol developed for this app is described bellow:

* Connection type: UDP (User Datagram Protocol)
* Max Buffer size: 1024 Bytes divided in: \
&emsp; **[action_status(2), packet_id (4), data(1002), checksum (16)]** 
    * 2    Bytes -> action_status ( \
    &emsp; &emsp; &emsp; 0xFF == OK \
    &emsp; &emsp; &emsp; 0xFA = File not found \
    &emsp; &emsp; &emsp; 0xAA = Bad request \
    &emsp; &emsp; &emsp; 0x80 == Internal error \
    &emsp; &emsp; )
    * 4    Bytes -> packet_id (number of the packet transmited)
    * 1002 Bytes -> data (max data buffer size)
    * 16   Bytes -> checksum (md5 checksum hash)
* Checksum: md5 hash checksum


Request: **ONLY accepts queries of type** \
    &emsp; **GET** filename (request a file) \
    &emsp; **ACK** packet_id (confirm acceptance of a packet) \
    &emsp; **RSD** packet_id (ask server to resend a packet) 


Response: \
    &emsp; [action_status(2), packet_id (4), data(1002), checksum (16)] 