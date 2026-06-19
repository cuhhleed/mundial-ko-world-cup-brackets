// E2-S4: Thin helper for Google Sign-In.
// @react-oauth/google's GoogleLogin onSuccess returns the ID token directly
// as credentialResponse.credential — no additional exchange needed.
// This module exists as a seam for future helpers (e.g. One Tap programmatic trigger).

export type GoogleCredentialResponse = {
  credential: string
}
