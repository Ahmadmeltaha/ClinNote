import { http, HttpResponse } from 'msw';

export const fixtures = {
  loginSuccess: {
    status: 200,
    data: {
      user: {
        id: '550e8400-e29b-41d4-a716-446655440000',
        email: 'john@example.com',
        displayName: 'John Doe',
        avatarColor: '#FF5733',
      },
      token:
        'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiI1NTBlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDAifQ.signature',
    },
  },
  loginInvalidCredentials: {
    status: 401,
    data: { error: 'Invalid email or password.' },
  },
  signupSuccess: {
    status: 200,
    data: {
      user: {
        id: '660e8400-e29b-41d4-a716-446655440001',
        email: 'alice@example.com',
        displayName: 'Alice Smith',
        avatarColor: '#3498DB',
      },
      token:
        'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiI2NjBlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDEifQ.signature2',
    },
  },
  signupConflict: {
    status: 409,
    data: { error: 'An account with this email already exists.' },
  },
  getProfile: {
    status: 200,
    data: {
      id: '550e8400-e29b-41d4-a716-446655440000',
      email: 'john@example.com',
      displayName: 'John Doe',
      avatarColor: '#FF5733',
      createdAt: '2024-01-01T00:00:00.000Z',
    },
  },
  updateProfile: {
    status: 200,
    data: {
      id: '550e8400-e29b-41d4-a716-446655440000',
      email: 'john@example.com',
      displayName: 'John Updated',
      avatarColor: '#FF5733',
      updatedAt: '2024-01-02T00:00:00.000Z',
    },
  },
  unauthorized: {
    status: 401,
    data: { error: 'Unauthorized' },
  },
};

export function createMockResponse(status: number, data: unknown): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText: status === 200 ? 'OK' : 'Error',
    headers: new Headers({ 'Content-Type': 'application/json' }),
    json: async () => data,
    text: async () => JSON.stringify(data),
    blob: async () => new Blob(),
    arrayBuffer: async () => new ArrayBuffer(0),
    formData: async () => new FormData(),
    bytes: async () => new Uint8Array(),
    clone: () => createMockResponse(status, data),
    redirected: false,
    type: 'basic' as ResponseType,
    url: '',
    body: null,
    bodyUsed: false,
  } as unknown as Response;
}

export const handlers = [
  http.post('*/api/auth/login', ({ request }) => {
    return HttpResponse.json(fixtures.loginSuccess.data, {
      status: fixtures.loginSuccess.status,
    });
  }),
  http.post('*/api/auth/signup', ({ request }) => {
    return HttpResponse.json(fixtures.signupSuccess.data, {
      status: fixtures.signupSuccess.status,
    });
  }),
  http.get('*/api/users/me', () => {
    return HttpResponse.json(fixtures.getProfile.data, {
      status: fixtures.getProfile.status,
    });
  }),
  http.patch('*/api/users/me', () => {
    return HttpResponse.json(fixtures.updateProfile.data, {
      status: fixtures.updateProfile.status,
    });
  }),
  http.post('*/api/auth/logout', () => {
    return HttpResponse.json({ success: true }, { status: 200 });
  }),
];
