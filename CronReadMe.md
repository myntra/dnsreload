//CRON WORKING

1. CRON calls the server to get all the records in JSON format.
eg JSON:[{
	status:"LIVE/ADDPENDING/UPDATEPENDING/DELETEPENDING",
	name:"example"
	value:"CNAME/IP" eg: "127.0.0.1" or "a1.example.com"
	type:"A/CNAME"
	ttl:"Seconds"
},
{}...]

2. It generates the conf files from the template for all the records after checking syntax with BIND 'named-checkzone'.

3. After generation of all the conf files, it generates the zone file.

4. The new generated zone file is checked against the original zone file , If there are any changes it calls the GIT_MODULE service to push the latest ZOne file to github repo

5. Before every changes to original zone file. Backup is made 