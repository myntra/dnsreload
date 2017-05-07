#CRON WORKING

* CRON calls the server to get all the records in JSON format.
eg JSON:
```
	[{
		status:"LIVE/ADDPENDING/UPDATEPENDING/DELETEPENDING",
		name:"example"
		value:"CNAME/IP" eg: "127.0.0.1" or "a1.example.com"
		type:"A/CNAME"
		ttl:"Seconds"
	},
	{}...]
```

* It generates the conf files from the template for all the records after checking syntax with BIND `named-checkzone`.

* After generation of all the conf files, it generates the zone file.

* The new generated zone file is checked against the original zone file , If there are any changes it calls the GIT_MODULE service to push the latest ZOne file to github repo

* Before every changes to original zone file. Backup is created.

* Set the GIT Repo parameters in the `appconfig.toml` and configs for creation of the records and storing backups in `configs.py`

* The `post_zone_change`function posts the status of all the records to the server from `status:"LIVE/ADDPENDING/UPDATEPENDING/DELETEPENDING"` to `status:"SUCCESS/FAILED"`. Based on whether they pass the BIND syntax  or not.
