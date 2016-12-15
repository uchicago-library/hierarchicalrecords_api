
# Available endpoints

## /record

### Methods: GET, POST

This endpoint when submitted via a GET request returns a list of all record identifiers in the system. When it is submitted via a POST request it creates a new hierarchical record in the system so longs as the POST request satisfies the minimal requirements for a hierarchical record.

## /record/[record identifier]

### Methods: GET, PUT, DELETE

When submitted  via a GET request, this endpoint will return either the complete record matching the identifier in the path or an error notifying the requester that the record could not be  found. When it is submitted via a PUT request, it will overwrite the record with the matching identifier with new information in the PUT data

## /record/[record identifier]/[field name]

### Methods: GET, POST, DELETE

When submitted via a GET request, it returns the  value of the field name for the record identified. When submitted via a POST request, it sets the value of the field enumerated for the record identified with the value defined in the POST data. When submitted via a DELETE request, it removes the field enumerated from the record identified.

## /validate

### Methods: POST

This returns a True or False whether the record identified in the POST data is valid against the configuration identified in the POST data.

## /conf

###  Methods: GET, POST

When submitted via a GET request, it returns a list of all configuration identifiers. When submitted via a POST request, it creates a new configuration record.

## /conf/[configuration record identifier]

### Methods: GET, POST, DELETE

When submitted via a GET request, it returns the configuration record identified. When submitted via a POST request, it adds the rule validation inputted in the POST request. When submitted via a DELETE request, it removes the identified configuration from the system.

## /conf/[configuration record identifier]/[rule identifier]

## Methods: GET, DELETE

When submitted via a GET requet, it returns the rule identified. When submitted via a DELETE request, it removes the rule identified from the configuration identified.

## /conf/[configuration record identifier]/[configuration record component name]

### Methods: GET, POST, DELETE

When submitted via a GET request, it returns the particular component of the rule in the configuration record identified. When submitted via a POST request, it adds a new rule component to the configuration record identifed. When submitted via a DELETe request, it removes the component named from the record configuration identified.

## /category

### Methods: GET, POST

When submitted via a GET request, it returns a list of all categories in the system. When submitted via a POST request, it adds a new category to the system with the identifier in the POST data.

## /category/[category identifier]

### Methods: GET, POST, DELETE

When submitted via a GET request, it returns the category record for the category identified. When submitted via a POST request it adds to the record identified in the POST data to the category identified. When submitted via a DELETE request, it removes the category identified from the system.

## /category/[category identifier]/[record identifier]

### Methods: GET, DELETE 

When submitted via a GET request, it returns whether or not a particular record is categorized in the category identified. When submitted via a DELETE request, it removes the record identified from the category identified.