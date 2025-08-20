# 💸 Expense Notify

Expense Notify is a demo project that helps streamline tracking of expenses and keeps track of whether each expense has been split with roommates.  
The app demonstrates modern backend patterns with authentication, event-driven design, and external integrations.

---

## ✨ Features

- 🔐 **JWT Authentication** – Secure signup and login with hashed passwords and access tokens.
- 📊 **CRUD Transactions** – Create, read, update, and delete expenses.
- 📧 **Gmail Integration** – Connect your Gmail account and automatically extract transactions from emails using **Gemini AI**, storing results in DynamoDB.
- 📡 **Event-Driven Architecture** – On every transaction **create** or **delete**, the app publishes a message to an **SNS topic**.
  - SQS queues and Lambdas use these messages for **notifications** and **analytics**.
- 🗄️ **DynamoDB Backend** – All transactions and user data are stored in AWS DynamoDB for scalability and performance.
- 🖥️ **Frontend App** – A modern **React + TypeScript** web app provides a clean UI for tracking and managing expenses.


---

## 🛠️ Tech Stack

**Backend**
- [FastAPI](https://fastapi.tiangolo.com/) (Python)
- JWT Authentication (bcrypt + passlib)
- AWS DynamoDB (database)
- AWS SNS + SQS (messaging)
- AWS Lambda (event consumers)
- Google OAuth (Gmail API)
- Gemini (Google Generative AI) for parsing transactions

**Frontend**
- [React](https://react.dev/) + [TypeScript](https://www.typescriptlang.org/)
- [Vercel](https://vercel.com/) for hosting
- Consumes the FastAPI backend via REST APIs
- Provides authentication, expense dashboard, Gmail linking
- [Github Link](https://github.com/jainryu/ExpenseNotifyFE)