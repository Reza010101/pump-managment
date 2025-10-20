import Constants from 'expo-constants';

type ApiLoginParams = { username: string; password: string };

function getApiBaseUrl(): string {
  const base = (Constants.expoConfig?.extra as any)?.apiBaseUrl as string | undefined;
  return base || 'http://10.0.2.2:5000';
}

export async function apiLogin(
  params: ApiLoginParams,
): Promise<{ success: boolean; error?: string; user?: any }> {
  const url = `${getApiBaseUrl()}/api/login`;
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(params),
    });
    const json = await res.json();
    if (!res.ok) {
      return { success: false, error: json?.error || 'Login failed' };
    }
    return json;
  } catch (e) {
    return { success: false, error: 'Network error' };
  }
}

export function apiGetBaseUrl(): string {
  return getApiBaseUrl();
}
