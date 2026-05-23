import { Amplify } from "aws-amplify";

export function configureAmplify(): void {
  Amplify.configure({
    Auth: {
      Cognito: {
        userPoolId: process.env.NEXT_PUBLIC_COGNITO_USER_POOL_ID ?? "",
        userPoolClientId:
          process.env.NEXT_PUBLIC_COGNITO_USER_POOL_CLIENT_ID ?? "",
        loginWith: {
          email: true,
        },
        userAttributes: {
          email: {
            required: true,
          },
        },
        mfa: {
          status: "optional",
          totpEnabled: false,
          smsEnabled: false,
        },
        passwordFormat: {
          minLength: 12,
          requireLowercase: true,
          requireUppercase: true,
          requireNumbers: true,
          requireSpecialCharacters: false,
        },
        signUpVerificationMethod: "code",
      },
    },
  });
}
