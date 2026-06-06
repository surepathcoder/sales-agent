"""Mock M-Pesa STK push for MVP."""

import uuid
from decimal import Decimal

from app.config import get_settings


class MPesaClient:
  """Simulates M-Pesa Daraja API — replace with real integration when funded."""

  def __init__(self) -> None:
    self.settings = get_settings()

  async def stk_push(
    self, phone: str, amount: Decimal, reference: str, callback_url: str
  ) -> dict:
    return {
      "CheckoutRequestID": f"ws_CO_{uuid.uuid4().hex[:20]}",
      "MerchantRequestID": reference,
      "ResponseCode": "0",
      "ResponseDescription": "Success. Request accepted for processing (MOCK)",
      "CustomerMessage": "Check your phone for M-Pesa prompt (simulated)",
      "mock": True,
      "amount": str(amount),
      "phone": phone,
    }

  async def query_status(self, checkout_request_id: str) -> dict:
    return {
      "ResultCode": "0",
      "ResultDesc": "The service request is processed successfully (MOCK)",
      "CheckoutRequestID": checkout_request_id,
    }
