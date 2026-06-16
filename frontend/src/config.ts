export const config = {
  apiUrl: import.meta.env.VITE_API_URL ?? "http://localhost:8000",
  aws: {
    region: import.meta.env.VITE_AWS_REGION ?? "",
    cognitoUserPoolId: import.meta.env.VITE_COGNITO_USER_POOL_ID ?? "",
    cognitoAppClientId: import.meta.env.VITE_COGNITO_APP_CLIENT_ID ?? "",
  },
};
