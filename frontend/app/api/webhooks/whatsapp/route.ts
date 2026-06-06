import { NextRequest, NextResponse } from 'next/server';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
  const body = await request.json();

  try {
    const res = await fetch(`${API_URL}/api/v1/webhooks/whatsapp`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (err) {
    console.error('WhatsApp webhook forward failed:', err);
    return NextResponse.json({ status: 'error' }, { status: 500 });
  }
}
