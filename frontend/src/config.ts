export const config = {
  apiUrl: import.meta.env.VITE_API_URL ?? "http://localhost:8000",
  googleClientId: import.meta.env.VITE_GOOGLE_CLIENT_ID ?? "",
  aws: {
    // TASK-001: remove Cognito fields when Cognito/SES is torn down
    region: import.meta.env.VITE_AWS_REGION ?? "",
    cognitoUserPoolId: import.meta.env.VITE_COGNITO_USER_POOL_ID ?? "",
    cognitoAppClientId: import.meta.env.VITE_COGNITO_APP_CLIENT_ID ?? "",
  },
};
