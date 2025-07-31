import json
from app.models.Email import Email
from app.models.Transaction import TransactionDB
from app.models.auth import UserInDB
from app.utils.prompt_utils import read_prompt


class Gemini:
    def __init__(self, client, model_name: str | None = "gemini-1.5-flash"):
        self.client = client
        self.model_name = model_name
        self.prompt = read_prompt("app/resources/gemini_prompt.txt")

    def get_transaction_from_gemini(self, user: UserInDB, emails: list[Email]) -> list[TransactionDB]:
        enumerated_transactions = [
            f"{i + 1}. {transaction}" for i, transaction in enumerate(emails)
        ]

        # prepare the prompt with the enumerated transactions
        prompt = self.prompt.replace("{enumerated_transactions}", str(
            enumerated_transactions)).replace("{user_id}", user.user_id)

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": list[TransactionDB],
            },
        )

        transaction_data = json.loads(response.text)
        transaction_list = [TransactionDB(**item) for item in transaction_data]

        return transaction_list
