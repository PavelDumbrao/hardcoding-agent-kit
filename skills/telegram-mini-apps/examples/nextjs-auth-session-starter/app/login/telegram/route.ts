// Канонический server-side entrypoint для browser fallback login.
// Не использовать прямой /api/auth/signin/... как user-facing ссылку.

import { signIn } from '@/lib/auth';

export async function GET() {
  return signIn('telegram', { redirectTo: '/profile' });
}
