import boto3


async def get_transactions():

    db = boto3.resource('dynamodb')
    table = db.Table('Transactions')

    