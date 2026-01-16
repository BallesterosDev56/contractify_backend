import { FastifyRequest, FastifyReply } from 'fastify';
import { initializeApp, cert, getApps, App } from 'firebase-admin/app';
import { getAuth } from 'firebase-admin/auth';
import { UnauthorizedError } from '../utils/errors.js';
import type { UserContext } from '../types/index.js';
import { config } from '../config/env.js';

declare module 'fastify' {
  interface FastifyRequest {
    user?: UserContext;
  }
}

let firebaseApp: App | null = null;

export function initializeFirebase(): void {
  if (getApps().length > 0) {
    firebaseApp = getApps()[0];
    return;
  }

  const { firebase } = config;

  if (!firebase.projectId || !firebase.privateKey || !firebase.clientEmail) {
    throw new Error('Firebase configuration is missing.');
  }

  firebaseApp = initializeApp({
    credential: cert({
      projectId: firebase.projectId,
      clientEmail: firebase.clientEmail,
      privateKey: firebase.privateKey.replace(/\\n/g, '\n'),
    }),
  });
}

export async function authenticateUser(
  request: FastifyRequest,
  _reply: FastifyReply
): Promise<void> {
  const authHeader = request.headers.authorization;

  if (!authHeader?.startsWith('Bearer ')) {
    throw new UnauthorizedError('Missing or invalid authorization header');
  }

  if (!firebaseApp) {
    initializeFirebase();
  }

  const token = authHeader.substring(7);

  try {
    const decodedToken = await getAuth(firebaseApp!).verifyIdToken(token);

    request.user = {
      userId: decodedToken.uid,
      email: decodedToken.email ?? '',
      role: decodedToken.role as string | undefined,
      claims: decodedToken,
    };
  } catch {
    throw new UnauthorizedError('Invalid or expired token');
  }
}

export async function optionalAuth(
  request: FastifyRequest,
  _reply: FastifyReply
): Promise<void> {
  const authHeader = request.headers.authorization;

  if (!authHeader?.startsWith('Bearer ')) {
    return;
  }

  if (!firebaseApp) {
    initializeFirebase();
  }

  try {
    const token = authHeader.substring(7);
    const decodedToken = await getAuth(firebaseApp!).verifyIdToken(token);

    request.user = {
      userId: decodedToken.uid,
      email: decodedToken.email ?? '',
      role: decodedToken.role as string | undefined,
      claims: decodedToken,
    };
  } catch {
    // silent
  }
}
