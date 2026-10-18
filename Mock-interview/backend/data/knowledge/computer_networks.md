# Computer Networks

## OSI model layers
The OSI model has seven layers, from bottom to top: Physical, Data Link, Network, Transport, Session, Presentation, Application. The TCP/IP model has four: Link (network access), Internet, Transport and Application.

## TCP vs UDP
TCP is connection-oriented and reliable: it sets up a connection, numbers and acknowledges segments, retransmits lost ones, delivers data in order, and does flow and congestion control. UDP is connectionless and unreliable: no handshake, no guarantee of delivery or order, but low overhead and latency. TCP suits web pages, email and file transfer; UDP suits DNS queries, video streaming, voice calls and online games.

## TCP three-way handshake
A TCP connection starts with three steps: the client sends SYN, the server replies SYN-ACK, and the client sends ACK. Closing a connection normally uses FIN and ACK exchanges in each direction (a four-step termination).

## HTTP vs HTTPS
HTTP sends data in plain text, by default on port 80. HTTPS is HTTP carried over TLS (formerly SSL), by default on port 443, which encrypts traffic, protects its integrity, and authenticates the server using a certificate.

## HTTP methods
GET retrieves a resource and has no side effects (safe and idempotent). POST creates a resource or submits data and is not idempotent. PUT replaces a resource and is idempotent. PATCH partially updates a resource. DELETE removes a resource and is idempotent.

## Common HTTP status codes
200 OK, 201 Created, 204 No Content, 301 Moved Permanently, 302 Found (temporary redirect), 400 Bad Request, 401 Unauthorized (not authenticated), 403 Forbidden (authenticated but not allowed), 404 Not Found, 500 Internal Server Error, 503 Service Unavailable. Classes: 2xx success, 3xx redirection, 4xx client error, 5xx server error.

## DNS
The Domain Name System translates human-readable domain names such as example.com into IP addresses. A resolver queries a hierarchy of servers (root, then top-level domain such as .com, then the authoritative name server) and caches the answer.

## What happens when you type a URL in the browser
The browser checks its cache, then resolves the domain to an IP address through DNS. It opens a TCP connection (three-way handshake) and, for HTTPS, performs a TLS handshake. It sends an HTTP request; the server processes it and returns a response; the browser parses the HTML, fetches CSS, JavaScript and images, and renders the page.

## IP address vs MAC address
An IP address is a logical address at the network layer that identifies a device on a network and can change with the network. A MAC address is a 48-bit physical hardware address at the data link layer, assigned to the network interface. IPv4 addresses are 32 bits; IPv6 addresses are 128 bits.

## ARP and DHCP
ARP (Address Resolution Protocol) maps an IP address to a MAC address on a local network. DHCP (Dynamic Host Configuration Protocol) automatically assigns IP addresses and related settings such as the gateway and DNS server to devices.

## Hub, switch and router
A hub (physical layer) repeats data to every port. A switch (data link layer) forwards frames to the correct port using MAC addresses. A router (network layer) forwards packets between different networks using IP addresses.

## Subnet mask and CIDR
A subnet mask separates the network part of an IP address from the host part. CIDR notation writes it as a prefix length, for example 192.168.1.0/24, meaning the first 24 bits identify the network and leave 8 bits (256 addresses) for hosts.

## Common port numbers
HTTP 80, HTTPS 443, SSH 22, FTP 21, SMTP 25, DNS 53, MySQL 3306, PostgreSQL 5432.

## Load balancer
A load balancer distributes incoming requests across several servers to improve availability and throughput and to avoid a single point of failure. Common strategies are round robin, least connections and IP hash.
