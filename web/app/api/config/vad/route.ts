import { NextResponse } from 'next/server';

const BACKEND_URL = 'http://localhost:8001';

export async function GET() {
  try {
    const res = await fetch(`${BACKEND_URL}/api/config/vad`);
    if (!res.ok) {
        // If backend returns 404 or other error, propagate it or return default
        if (res.status === 404) {
             return NextResponse.json({
                voice_threshold: 500,
                silence_threshold: 200
            });
        }
        throw new Error(`Backend error: ${res.statusText}`);
    }
    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error fetching VAD config:", error);
    return NextResponse.json({ error: 'Failed to fetch config' }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const res = await fetch(`${BACKEND_URL}/api/config/vad`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    
    if (!res.ok) {
        throw new Error(`Backend error: ${res.statusText}`);
    }
    
    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error saving VAD config:", error);
    return NextResponse.json({ error: 'Failed to save config' }, { status: 500 });
  }
}
