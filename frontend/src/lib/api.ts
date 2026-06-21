import { fetchAuthSession } from "aws-amplify/auth";

async function authHeader(): Promise<Record<string, string>> {
  try {
    const session = await fetchAuthSession();
    const token = session.tokens?.accessToken?.toString();
    return token ? { Authorization: `Bearer ${token}` } : {};
  } catch {
    return {};
  }
}

export async function apiFetch(
  input: string,
  init: RequestInit = {},
): Promise<Response> {
  const auth = await authHeader();
  const headers = new Headers(init.headers);
  for (const [k, v] of Object.entries(auth)) {
    headers.set(k, v);
  }
  return fetch(input, { ...init, headers });
}
