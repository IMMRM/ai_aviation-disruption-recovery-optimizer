from groq import Groq
import os

from config.settings import (
    GROQ_API_KEY
)

class RecoveryChatService:

    def __init__(self):

        if not GROQ_API_KEY:

            self.client = None

        else:

            self.client = Groq(
                api_key=GROQ_API_KEY
            )

    def ask(

        self,

        question: str,

        recovery_context: str
    ):

        try:

            if not self.client:

                return (
                    "❌ Groq API Error: "
                    "GROQ_API_KEY is not configured. "
                    "Please add GROQ_API_KEY to your .env file."
                )

            if not recovery_context:

                return (
                    "Recovery context is missing. "
                    "Please run optimization first."
                )

            if not question:

                return (
                    "Please ask a question."
                )

            response = self.client.chat.completions.create(

                model="openai/gpt-oss-120b",

                messages=[

                    {
                        "role": "system",

                        "content":
                        """Be a brief Operations Recovery Analyst.

Answer ONLY using provided recovery data.

For "Why was X assigned?" questions:
- State the aircraft & reason (2-3 facts)
- Reference proximity, cost, delay
- Keep it 2-3 sentences max

For "Why wasn't X assigned?" questions:
- Explain: Only 1 aircraft per flight
- Reference the assigned aircraft & why it was chosen
- Mention that other aircraft were either:
  * Infeasible (unavailable/capacity/time)
  * More expensive
  * Conflicted with other assignments

For cost questions:
- Quote specific recovery cost & components

If info unavailable: "Not available in recovery data."

Be factual. No assumptions. Keep responses SHORT."""
                    },

                    {
                        "role": "user",

                        "content":
                        f"""

                        Recovery Context:

                        {recovery_context}

                        Question:

                        {question}

                        """
                    }
                ],

                temperature=0.5,

                max_tokens=200
            )

            return (
                response
                .choices[0]
                .message
                .content
            )

        except Exception as e:

            error_msg = str(e)

            if "authentication" in error_msg.lower():

                return (
                    "❌ Authentication Error: "
                    "GROQ_API_KEY is invalid. "
                    "Please check your .env file."
                )

            elif "rate_limit" in error_msg.lower():

                return (
                    "⏳ Rate Limit: "
                    "Too many requests. "
                    "Please try again in a moment."
                )

            else:

                return (
                    f"❌ Error: {error_msg}"
                )