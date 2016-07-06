# hierarchicalrecords_api

In development

## Endponts

| End Point                                                 | HTTP Method | Action                                                                    | Data                                                                                     | Response Data                                                                                                                                                                | Notes                       |

|-----------------------------------------------------------|-------------|---------------------------------------------------------------------------|------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------|

| /record                                                   | GET         | Retrieve a list of all record identifiers                                 | X                                                                                        | {"records":  <list:identifiers>}                                                                                                                                             |                             |

| /record                                                   | POST        | Create a new record. Populate it's original data with the supplied if any | record (o): <dict:record>conf (o): <str:conf_identifier>                                 | {"identifier": <str:identifier>, "record": <dict:record>}                                                                                                                    |                             |

| /record                                                   | DELETE      | Delete all records                                                        | X                                                                                        | {"deleted_identifiers": <list:identifiers>}                                                                                                                                  |                             |

| /record/<string:identifier>                               | GET         | Retrieve a record                                                         | X                                                                                        | {"record": <dict:record>, "identifier": <str:identifier>}                                                                                                                    |                             |

| /record/<string:identifier>                               | PUT         | Overwrite a record                                                        | record (r): <dict:record>conf (o): <str:conf_identifier>                                 | {"record": <dict:record>, "identifier": <str:identifier>}                                                                                                                    |                             |

| /record/<string:identifier>                               | DELETE      | Delete a record                                                           | X                                                                                        | {"identifier": <str:identifier>}                                                                                                                                             |                             |

| /record/<string:identifier>/<string:key>                  | GET         | Get a value in a record                                                   | X                                                                                        | {"record_identifier: <str:record_identifier>, "key": <str:key>, "value": <value>}                                                                                            |                             |

| /record/<string:identifier>/<string:key>                  | POST        | Set a value in a record                                                   | value(r): <the value>conf (o): <str:conf_identifier>                                     | {"record": <dict:record>, "identifier": <str:identifier>}                                                                                                                    |                             |

| /record/<string:identifier>/<string:key>                  | DELETE      | Delete a value in a record                                                | conf (o): <str:conf_identifier>                                                          | {"record": <dict:record>, "identifier": <str:identifier>}                                                                                                                    |                             |

| /validate                                                 | POST        | Validate a record against a conf                                          | record_identifier (r): <str:record_identifier>conf_identifier (r): <str:conf_identifier> | {"is_valid": <bool:validity>, "validation_errors":<null||list:error messages>, "identifier": <str:record_identifier>, "conf": <str:conf_identifier>, "record":<dict:record>} |                             |

| /conf                                                     | GET         | Get a list of all conf identifiers                                        | X                                                                                        | {"confs": <list:conf_identifiers>}                                                                                                                                           |                             |

| /conf/<string:identifier>                                 | GET         | Get a specific conf                                                       | X                                                                                        | {"identifier": <str:conf_identifier>, "conf": <dict:conf data>}                                                                                                              |                             |

| /category                                                 | GET         | Get a list of all categories                                              | X                                                                                        | {"categories": <list:category_identifiers>}                                                                                                                                  |                             |

| /category                                                 | POST        | Create a new category                                                     | conf_id (r): <str:conf_identifier>records (o): <list: list of record_identifiers>        | {"category": <str:category_identifier>, "records": <list:category_records>}                                                                                                  |                             |

| /category/<string:cat_identifier>                         | GET         | Get a list of all record identifiers in a specific category               | X                                                                                        | {"category": <str:category_identifier>, "records": <list:category_records>}                                                                                                  |                             |

| /category/<string:cat_identifier>                         | PUT         | Replace all records in a category                                         | records (r): <list:record_identifiers>                                                   | {"category": <str:category_identifier>, "records": <list:category_records>}                                                                                                  |                             |

| /category/<string:cat_identifier>                         | POST        | Add a record to a category                                                | record_identifier (r): <str:record_identifier>                                           | {"category": <str:category_identifier>, "records": <list:category_records>}                                                                                                  |                             |

| /category/<string:cat_identifier>                         | DELETE      | Delete a category                                                         | X                                                                                        | {"categories": <list:category_identifiers>}                                                                                                                                  |                             |

| /category/<string:cat_identifier>/<string:rec_identifier> | GET         | Determine if a record is in a category                                    | X                                                                                        | {"category": <str:category_identifier>, "records": <list:category_records>, "record_present": <bool:true>}                                                                   | fails if record not present |

| /category/<string:cat_identifier>/<string:rec_identifier> | DELETE      | Remove a record from a category                                           | X                                                                                        | {"category": <str:category_identifier>, "records": <list:category_records>}                                                                                                  |                             |
