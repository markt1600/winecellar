import {cookies} from 'next/headers';
export const headers = {'Cache-Control':'private, no-store','Vary':'Cookie'};
export async function isOwner() {
  const token = (await cookies()).get('__Secure-mt_camera')?.value;
  if (!token || token.length > 1024 || !/^[A-Za-z0-9_.-]+$/.test(token)) return false;
  try {
    // Existing owner-only service verifies its own cookie. No shared secret is copied.
    const r = await fetch('https://security.marktan.ai/api/session', {
      headers: {Cookie: `__Secure-mt_camera=${token}`}, cache:'no-store',
      redirect:'error', signal:AbortSignal.timeout(8000)
    });
    return r.status === 200 && (await r.json()).ok === true;
  } catch { return false; }
}
