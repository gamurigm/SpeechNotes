import { NextRequest } from 'next/server';

// In Docker, API_URL points to the backend service name. The public URL is
// only appropriate for browser-side requests and is not reachable from the
// frontend container itself.
const BACKEND_URL = process.env.API_URL || process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:9443';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    // Forward request to backend streaming endpoint
    const response = await fetch(`${BACKEND_URL}/api/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': 'dev-secret-api-key',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      throw new Error(`Backend error: ${response.statusText}`);
    }

    // Return the streaming response
    return new Response(response.body, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    });
  } catch (error) {
    console.error('Chat API error:', error);
    return new Response(
      JSON.stringify({ error: 'Failed to process chat request' }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
}
