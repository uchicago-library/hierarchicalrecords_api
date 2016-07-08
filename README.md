# hierarchicalrecords_api

In development

## Endpoints

* Entries in the data column are expected to be either JSON keys if the request contains "Content-Type: application/json" in the header, or url-encoded onto the request to the endpoint.

* Data values can either be required (r) or optional (o)

* An "X" in a data field implies that the endpoint/method accepts no data.

| End Point | HTTP Method | Action | Data | Response Data | Notes |
|---------------------------------------------------------------|-------------|---------------------------------------------------------------------------|------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------|
| /record | GET | Retrieve a list of all record identifiers | X | {"record_identifiers":  \<list:identifiers\>} |  |
| /record | POST | Create a new record. Populate it's original data with the supplied if any | record (o): \<dict:record\>conf_identifier (o): \<str:conf_identifier\> | {"record_identifier": \<str:identifier\>, "record": \<dict:record\>} |  |
| /record/\<string:identifier\> | GET | Retrieve a record | X | {"record": \<dict:record\>, "record_identifier": \<str:identifier\>} |  |
| /record/\<string:identifier\> | PUT | Overwrite a record | record (r): \<dict:record\>conf_identifier (o): \<str:conf_identifier\> | {"record": \<dict:record\>, "record_identifier": \<str:identifier\>} |  |
| /record/\<string:identifier\> | DELETE | Delete a record | X | {"records":  \<list:identifiers\> "deleted_identifier": \<str:identifier\>} |  |
| /record/\<string:identifier\>/\<string:key\> | GET | Get a value in a record | X | {"record_identifier: \<str:record_identifier\>, "key": \<str:key\>, "value": \<value\>} |  |
| /record/\<string:identifier\>/\<string:key\> | POST | Set a value in a record | value (r): \<the value\>conf_identifier (o): \<str:conf_identifier\> | {"record": \<dict:record\>, "record_identifier": \<str:identifier\>} |  |
| /record/\<string:identifier\>/\<string:key\> | DELETE | Delete a value in a record | conf_identifier (o): \<str:conf_identifier\> | {"record": \<dict:record\>, "record_identifier": \<str:identifier\>} |  |
| /validate | POST | Validate a record against a conf | record_identifier (r): \<str:record_identifier\>conf_identifier (r): \<str:conf_identifier\> | {"is_valid": \<bool:validity\>, "validation_errors":\<null||list:error messages\>, "record_identifier": \<str:record_identifier\>, "conf_identifier": \<str:conf_identifier\>, "record":\<dict:record\>} |  |
| /conf | GET | Get a list of all conf identifiers | X | {"conf_identifiers": \<list:conf_identifiers\>} |  |
| /conf | POST | Create a new conf | X | {"conf_identifier": \<str:conf_identifier\>, "conf": \<dict:conf data\>} |  |
| /conf/\<string:identifier\> | GET | Get a specific conf | X | {"conf_identifier": \<str:conf_identifier\>, "conf": \<dict:conf data\>} |  |
| /conf/\<string:identifier\> | POST | set a validation rule | rule (r): \<dict:rule_dict\> | {"conf_identifier": \<str:conf_identifier\>, "conf": \<dict:conf data\>} |  |
| /conf/\<string:identifier\> | DELETE | delete a validation rule | X | {"conf_identifiers": \<list:conf_identifiers\>, "deleted_conf_identifier": \<str:deleted_identifier\>} |  |
| /conf/\<string:identifier\>/\<string:rule_id\> | GET | get a specific rule | X | {"conf_identifier": \<str:conf_identifier\>, "rule": \<str:rule_value\>} |  |
| /conf/\<string:identifier\>/\<string:rule_id\> | DELETE | delete a rule from a conf | X | {"conf_identifier": \<str:conf_identifier\>, "conf": \<dict:conf data\>} |  |
| /conf/\<string:identifier\>/\<string:rule_id\>/\<string:component\> | GET | Get a rule component | X | {“conf_identifier”: \<string:conf_identifier\>, “rule_id”: \<string:rule_id\>, “component”: \<string:component\>, “value”: \<str:value\>} |  |
| /conf/\<string:identifier\>/\<string:rule_id\>/\<string:component\> | POST | Set a rule component | component_value (r) : \<str:component_value\> | {“conf_identifier”: \<string:conf_identifier\>, “rule_id”: \<string:rule_identifier\>, “component”: \<string:component\>, “value”: \<string:component_value\>} |  |
| /conf/\<string:identifier\>/\<string:rule_id\>/\<string:component\> | DELETE | Delete a rule component | X | {“conf_identifier”: \<string:conf_identifier\>, “rule_id”: \<string:rule_identifier\>, “component”: \<string:component\>, “value”: \<string:component_value\>} |  |
| /category | GET | Get a list of all categories | X | {"category_identifiers": \<list:category_identifiers\>} |  |
| /category | POST | Create a new category | category_identifier (r): \<str:cat_identifier\> | {"category_identifier": \<str:category_identifier\>, "record_identifiers": \<list:category_records\>} |  |
| /category/\<string:cat_identifier\> | GET | Get a list of all record identifiers in a specific category | X | {"category_identifier": \<str:category_identifier\>, "record_identifiers": \<list:category_records\>} |  |
| /category/\<string:cat_identifier\> | POST | Add a record to a category | record_identifier (r): \<str:record_identifier\> | {"category_identifier": \<str:category_identifier\>, "record_identifiers": \<list:category_records\>} |  |
| /category/\<string:cat_identifier\> | DELETE | Delete a category | X | {"category_identifiers": \<list:category_identifiers\>} |  |
| /category/\<string:cat_identifier\>/\<string:rec_identifier\> | GET | Determine if a record is in a category | X | {"category": \<str:category_identifier\>, "records": \<list:category_records\>, "record_present": \<bool:true\>} | fails if record not present |
| /category/\<string:cat_identifier\>/\<string:rec_identifier\> | DELETE | Remove a record from a category | X | {"category_identifier": \<str:category_identifier\>, "record_identifiers": \<list:category_records\>} |  |
