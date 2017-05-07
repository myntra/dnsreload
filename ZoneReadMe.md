//TO work with DNS BIND SERVER

1. Register your zone in the /etc/named.conf :
	zone "<ZONE_ADDR>" IN {
	type master;
	file "<ZONE_FILE";
	allow-update { none; };
	};

2. Create ZONE_FILE in /var/named/ directory :
	$TTL 86400
	@   IN  SOA     masterdns.<ZONE_ADDR>. root.<ZONE_ADDR>. (
	        1  ;Serial
	        3600        ;Refresh
	        1800        ;Retry
	        604800      ;Expire
	        86400       ;Minimum TTL
	)
	@       IN  NS          masterdns.<ZONE_ADDR>.
	@       IN  A           <DNS_SERVER_IP>
	
	<RECORD_NAME> <RECORD_TTL> <RECORD_TYPE> <RECORD_VALUE> eg : odin 1800 IN A 192.20.20.12
	.
	.
	.

3. Enable and start the DNS Name service : 
	systemctl enable named
	systemctl start named

4. Check DNS default configuration file:
	named-checkconf /etc/named.conf

5. Check the syntax of ZONE_FILE : 
	named-checkzone <ZONE_LABEL> /var/named/<ZONE_FILE>

6. Add DNS SERVER entry in /etc/resolv.conf :
	nameserver <DNS_SERVER_IP>

7. Restart the Named service after every modification to named directory:
	systemctl restart named.service

8. To test the DNS Server. dig any <RECORD_NAME>.<ZONE_ADDR>:
	if answer section along with authorative section having NameServer address as <DNS_SERVER_IP> comes, The DNS is working correctly.