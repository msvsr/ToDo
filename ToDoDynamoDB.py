import boto3
dynamodb = boto3.client("dynamodb")


def create_table(params=None):
    if params is None:
        params = {}

    if params:
        existing_tables = dynamodb.list_tables()['TableNames']
        if not params["TableName"] in existing_tables:
            try:
                dynamodb.create_table(**params)
            except Exception as e:
                print(e)
        else:
            print("Table already exists")


table_creation_params = {
    "AttributeDefinitions": [
        {
            'AttributeName': 'userid',
            'AttributeType': 'S'
        },
        {
            'AttributeName': 'TodoId',
            'AttributeType': 'S'
        }
    ],
    "KeySchema": [
        {
            'AttributeName': 'userid',
            'KeyType': 'HASH'
        },
        {
            'AttributeName': 'TodoId',
            'KeyType': 'RANGE'
        }
    ],
    "ProvisionedThroughput": {
        'ReadCapacityUnits': 5,
        'WriteCapacityUnits': 5,
    },
    "TableName": 'ToDo'
}

create_table(table_creation_params)
"""
Attributes:

All are strings:
userid
TodoId
TodoDescription
CompletionStatus
CompletionDateTime
CreationDateTime

"""
