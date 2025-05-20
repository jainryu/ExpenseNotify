import json
from app.models.Transaction import Transaction

class Gemini:
    def __init__(self, client, model_name: str | None = "gemini-1.5-flash"):
        self.client = client
        self.model_name = model_name

    def get_transaction_from_gemini(self, transactions: list[str]) -> list[Transaction]:
        enumerated_transactions = [
            f"{i + 1}. {transaction}" for i, transaction in enumerate(transactions)
        ]
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=f"Given the list of transaction, create the list of transactions in the format of JSON. The list of transactions are: {enumerated_transactions}. There should be only one trasnsaction object per each transaction. The description of the transaction should be at most 50 characters. Use the first element as an id",
            config={
                "response_mime_type": "application/json",
                "response_schema": list[Transaction],
            },
        )

        transaction_data = json.loads(response.text)
        transaction_list = [Transaction(**item) for item in transaction_data]

        return transaction_list