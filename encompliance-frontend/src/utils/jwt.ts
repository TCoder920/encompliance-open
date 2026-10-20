/*
  Description: Lightweight JWT helpers for client-side token validation.
  Purpose: Decode JWT payloads and determine expiration without verifying signature.
*/

interface JwtPayload {
  exp?: number;
  [key: string]: unknown;
}

const decodeSegment = (segment: string): string => {
  const padded = segment.padEnd(segment.length + ((4 - (segment.length % 4)) % 4), '=');
  try {
    return atob(padded.replace(/-/g, '+').replace(/_/g, '/'));
  } catch {
    return '';
  }
};

export const decodeJwtPayload = (token: string): JwtPayload | null => {
  if (!token) {
    return null;
  }
  const parts = token.split('.');
  if (parts.length < 2) {
    return null;
  }
  try {
    return JSON.parse(decodeSegment(parts[1]));
  } catch {
    return null;
  }
};

export const isJwtExpired = (token: string, skewMs = 0): boolean => {
  const payload = decodeJwtPayload(token);
  if (!payload || typeof payload.exp !== 'number') {
    return true;
  }
  const expiresAt = payload.exp * 1000;
  return Date.now() + skewMs >= expiresAt;
};


